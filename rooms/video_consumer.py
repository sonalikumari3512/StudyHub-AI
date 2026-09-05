import json

from channels.generic.websocket import AsyncWebsocketConsumer


class VideoConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]

        self.video_group_name = f"video_{self.room_id}"

        # Check authentication
        if not self.user.is_authenticated:
            await self.close()
            return

        # Join video group
        await self.channel_layer.group_add(
            self.video_group_name,
            self.channel_name
        )

        await self.accept()

        print(
            f"🎥 Video connected: "
            f"{self.user.username} "
            f"(ID: {self.user.id})"
        )

        # Tell other users that this user joined
        await self.channel_layer.group_send(
            self.video_group_name,
            {
                "type": "user_joined",
                "user_id": self.user.id,
                "username": self.user.username,
            }
        )


    async def disconnect(self, close_code):

        if hasattr(self, "video_group_name"):

            await self.channel_layer.group_discard(
                self.video_group_name,
                self.channel_name
            )

            # Tell other users this user left
            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    "type": "user_left",
                    "user_id": self.user.id,
                    "username": self.user.username,
                }
            )

        print(
            f"👋 Video disconnected: "
            f"{self.user.username}"
        )


    async def receive(self, text_data):

        data = json.loads(text_data)

        event_type = data.get("type")

        print(
            f"📨 Video signal from "
            f"{self.user.username}: {event_type}"
        )


        # =========================================
        # OFFER
        # =========================================

        if event_type == "offer":

            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    "type": "video_offer",
                    "offer": data.get("offer"),
                    "sender_id": self.user.id,
                }
            )


        # =========================================
        # ANSWER
        # =========================================

        elif event_type == "answer":

            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    "type": "video_answer",
                    "answer": data.get("answer"),
                    "sender_id": self.user.id,
                }
            )


        # =========================================
        # ICE CANDIDATE
        # =========================================

        elif event_type == "ice_candidate":

            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    "type": "ice_candidate",
                    "candidate": data.get("candidate"),
                    "sender_id": self.user.id,
                }
            )


    # =============================================
    # USER JOINED
    # =============================================

    async def user_joined(self, event):

        # Don't send to the user who joined
        if event["user_id"] == self.user.id:
            return

        await self.send(
            text_data=json.dumps({
                "type": "user_joined",
                "user_id": event["user_id"],
                "username": event["username"],
            })
        )


    # =============================================
    # USER LEFT
    # =============================================

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


    # =============================================
    # VIDEO OFFER
    # =============================================

    async def video_offer(self, event):

        # Don't send offer back to sender
        if event["sender_id"] == self.user.id:
            return

        print(
            f"📤 Sending OFFER to "
            f"{self.user.username}"
        )

        await self.send(
            text_data=json.dumps({
                "type": "offer",
                "offer": event["offer"],
                "sender_id": event["sender_id"],
            })
        )


    # =============================================
    # VIDEO ANSWER
    # =============================================

    async def video_answer(self, event):

        # Don't send answer back to sender
        if event["sender_id"] == self.user.id:
            return

        print(
            f"📤 Sending ANSWER to "
            f"{self.user.username}"
        )

        await self.send(
            text_data=json.dumps({
                "type": "answer",
                "answer": event["answer"],
                "sender_id": event["sender_id"],
            })
        )


    # =============================================
    # ICE CANDIDATE
    # =============================================

    async def ice_candidate(self, event):

        # Don't send ICE back to sender
        if event["sender_id"] == self.user.id:
            return

        await self.send(
            text_data=json.dumps({
                "type": "ice_candidate",
                "candidate": event["candidate"],
                "sender_id": event["sender_id"],
            })
        )

