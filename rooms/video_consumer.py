import json

from channels.generic.websocket import AsyncWebsocketConsumer

# Simple in-memory room tracking.
# room_id -> { user_id: {"channel_name": ..., "username": ...} }
active_rooms = {}


class VideoConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.video_group_name = f"video_{self.room_id}"

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.video_group_name,
            self.channel_name
        )

        await self.accept()

        room = active_rooms.setdefault(self.room_id, {})

        # Send the new user the list of everyone ALREADY in the room
        existing_users = [
            {"user_id": uid, "username": info["username"]}
            for uid, info in room.items()
            if uid != self.user.id
        ]

        await self.send(
            text_data=json.dumps({
                "type": "room_users",
                "users": existing_users,
            })
        )

        # Now register this user in the room
        room[self.user.id] = {
            "channel_name": self.channel_name,
            "username": self.user.username,
        }

        # Tell everyone ELSE that a new user joined
        await self.channel_layer.group_send(
            self.video_group_name,
            {
                "type": "user_joined",
                "user_id": self.user.id,
                "username": self.user.username,
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.video_group_name,
            self.channel_name
        )

        room = active_rooms.get(self.room_id)
        if room and self.user.id in room:
            del room[self.user.id]
            if not room:
                del active_rooms[self.room_id]

        await self.channel_layer.group_send(
            self.video_group_name,
            {
                "type": "user_left",
                "user_id": self.user.id,
                "username": self.user.username,
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get("type")

        if event_type == "offer":
            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    "type": "video_offer",
                    "offer": data.get("offer"),
                    "sender_id": self.user.id,
                    "target_id": data.get("target_id"),
                }
            )

        elif event_type == "answer":
            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    "type": "video_answer",
                    "answer": data.get("answer"),
                    "sender_id": self.user.id,
                    "target_id": data.get("target_id"),
                }
            )

        elif event_type == "ice_candidate":
            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    "type": "ice_candidate",
                    "candidate": data.get("candidate"),
                    "sender_id": self.user.id,
                    "target_id": data.get("target_id"),
                }
            )

    async def user_joined(self, event):
        if event["user_id"] == self.user.id:
            return

        await self.send(
            text_data=json.dumps({
                "type": "user_joined",
                "user_id": event["user_id"],
                "username": event["username"],
            })
        )

    async def user_left(self, event):
        if event["user_id"] == self.user.id:
            return

        await self.send(
            text_data=json.dumps({
                "type": "user_left",
                "user_id": event["user_id"],
                "username": event["username"],
            })
        )

    async def video_offer(self, event):
        if event["target_id"] != self.user.id:
            return

        await self.send(
            text_data=json.dumps({
                "type": "offer",
                "offer": event["offer"],
                "sender_id": event["sender_id"],
            })
        )

    async def video_answer(self, event):
        if event["target_id"] != self.user.id:
            return

        await self.send(
            text_data=json.dumps({
                "type": "answer",
                "answer": event["answer"],
                "sender_id": event["sender_id"],
            })
        )

    async def ice_candidate(self, event):
        if event["target_id"] != self.user.id:
            return

        await self.send(
            text_data=json.dumps({
                "type": "ice_candidate",
                "candidate": event["candidate"],
                "sender_id": event["sender_id"],
            })
        )