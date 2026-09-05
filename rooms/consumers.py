import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from django.contrib.auth.models import User
from django.utils import timezone

from .models import Room, Message
from users.models import UserProfile,Notification


class ChatConsumer(AsyncWebsocketConsumer):

    # ==========================================
    # CONNECT
    # ==========================================

    async def connect(self):

        self.user = self.scope["user"]

        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]

        self.room_group_name = f"room_{self.room_id}"

        if not self.user.is_authenticated:

            await self.close()

            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.set_online(True)

        count = await self.get_online_count()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "online_count",
                "count": count
            }
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "presence",
                "user_id": self.user.id,
                "username": self.user.username,
                "online": True,
                "last_seen": ""
            }
        )

    # ==========================================
    # DISCONNECT
    # ==========================================

    async def disconnect(self, close_code):

        await self.set_online(False)

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        last_seen = timezone.localtime().strftime("%d %b %I:%M %p")

        count = await self.get_online_count()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "online_count",
                "count": count
            }
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "presence",
                "user_id": self.user.id,
                "username": self.user.username,
                "online": False,
                "last_seen": last_seen
            }
        )

    # ==========================================
    # RECEIVE
    # ==========================================

    async def receive(self, text_data):

        data = json.loads(text_data)

        event = data.get("type")

        if event == "message":

            await self.create_message(data)

        elif event == "edit":

            await self.edit_message_event(data)

        elif event == "delete":

            await self.delete_message_event(data)

        elif event == "typing":

            await self.channel_layer.group_send(

                self.room_group_name,

                {
                    "type": "typing_status",
                    "username": self.user.username,
                    "typing": data.get("typing", False)
                }

            )

        elif event == "delivered":

            await self.mark_delivered(data)

        elif event == "read":

            await self.mark_read(data)
        # ==========================================
    # CREATE MESSAGE
    # ==========================================

    async def create_message(self, data):

        text = data.get("message", "").strip()

        if not text:
            return

        message = await self.save_message(text)

        await self.channel_layer.group_send(

            self.room_group_name,

            {
                "type": "chat_message",

                "id": message.id,

                "message": message.body,

                "username": self.user.username,

                "user_id": self.user.id,

                "time": timezone.localtime(
                    message.created_at
                ).strftime("%d %b %Y, %I:%M %p"),

                "delivered": False,

                "read": False,
            },
        )

        await self.send_notifications(message)


    # ==========================================
    # EDIT MESSAGE
    # ==========================================

    async def edit_message_event(self, data):

        msg = await self.update_message(

            data.get("message_id"),

            data.get("message", "")

        )

        if not msg:
            return

        await self.channel_layer.group_send(

            self.room_group_name,

            {
                "type": "edited",

                "id": msg.id,

                "message": msg.body,
            },
        )


    # ==========================================
    # DELETE MESSAGE
    # ==========================================

    async def delete_message_event(self, data):

        deleted = await self.delete_message(

            data.get("message_id")
        )

        if not deleted:
            return

        await self.channel_layer.group_send(

            self.room_group_name,

            {
                "type": "deleted",

                "id": data.get("message_id"),
            },
        )


    # ==========================================
    # SEND MESSAGE TO ALL
    # ==========================================

    async def chat_message(self, event):

        await self.send(

            text_data=json.dumps(

                {
                    "type": "message",

                    "id": event["id"],

                    "message": event["message"],

                    "username": event["username"],

                    "user_id": event["user_id"],

                    "time": event["time"],

                    "delivered": event["delivered"],

                    "read": event["read"],
                }

            )

        )


    # ==========================================
    # MESSAGE EDITED
    # ==========================================

    async def edited(self, event):

        await self.send(

            text_data=json.dumps(

                {
                    "type": "edited",

                    "id": event["id"],

                    "message": event["message"],
                }

            )

        )


    # ==========================================
    # MESSAGE DELETED
    # ==========================================

    async def deleted(self, event):

        await self.send(

            text_data=json.dumps(

                {
                    "type": "deleted",

                    "id": event["id"],
                }

            )

        )


    # ==========================================
    # TYPING
    # ==========================================

    async def typing_status(self, event):

        await self.send(

            text_data=json.dumps(

                {
                    "type": "typing",

                    "username": event["username"],

                    "typing": event["typing"],
                }

            )

        )


    # ==========================================
    # USER PRESENCE
    # ==========================================

    async def presence(self, event):

        await self.send(

            text_data=json.dumps(

                {
                    "type": "presence",

                    "user_id": event["user_id"],

                    "username": event["username"],

                    "online": event["online"],

                    "last_seen": event["last_seen"],
                }

            )

        )


    # ==========================================
    # ONLINE COUNT
    # ==========================================

    async def online_count(self, event):

        await self.send(

            text_data=json.dumps(

                {
                    "type": "online_count",

                    "count": event["count"],
                }

            )

        )
        # ==========================================
    # DATABASE HELPERS
    # ==========================================

    @database_sync_to_async
    def save_message(self, text):

        room = Room.objects.get(id=self.room_id)

        return Message.objects.create(

            room=room,
            user=self.user,
            body=text

        )


    @database_sync_to_async
    def update_message(self, message_id, text):
        try:
            # Cast message_id to int to ensure database query matches
            msg = Message.objects.get(
                id=int(message_id),
                user=self.user
            )
            msg.body = text
            msg.save()
            return msg
        except (Message.DoesNotExist, ValueError, TypeError):
            return None

    @database_sync_to_async
    def delete_message(self, message_id):

        try:

            msg = Message.objects.get(

                id=message_id,
                user=self.user

            )

            msg.delete()

            return True

        except Message.DoesNotExist:

            return False


    # ==========================================
    # DELIVERED
    # ==========================================

    async def mark_delivered(self, data):

        await self.channel_layer.group_send(

            self.room_group_name,

            {

                "type": "delivered_status",

                "id": data["message_id"]

            }

        )


    async def delivered_status(self, event):

        await self.send(

            text_data=json.dumps(

                {

                    "type": "delivered",

                    "id": event["id"]

                }

            )

        )


    # ==========================================
    # READ
    # ==========================================

    async def mark_read(self, data):

        await self.channel_layer.group_send(

            self.room_group_name,

            {

                "type": "read_status",

                "id": data["message_id"]

            }

        )


    async def read_status(self, event):

        await self.send(

            text_data=json.dumps(

                {

                    "type": "read",

                    "id": event["id"]

                }

            )

        )


    # ==========================================
    # USER ONLINE/OFFLINE
    # ==========================================

    @database_sync_to_async
    def set_online(self, online):

        profile, created = UserProfile.objects.get_or_create(

            user=self.user

        )

        profile.is_online = online

        profile.last_seen = timezone.now()

        profile.save()


    @database_sync_to_async
    def get_online_count(self):

        room = Room.objects.get(id=self.room_id)

        return room.members.filter(

            userprofile__is_online=True

        ).count()


    # ==========================================
    # SAVE CHAT NOTIFICATION
    # ==========================================

    @database_sync_to_async
    def save_chat_notification(self, receiver, room, message):

        Notification.objects.create(
            user=receiver,
            title=f"New message in {room.name}",
            message=f"{self.user.username}: {message.body}",
            notification_type="chat",
            link=f"/rooms/{room.id}/"
        )

    # ==========================================
    # SEND NOTIFICATIONS
    # ==========================================

    async def send_notifications(self, message):

        room = await database_sync_to_async(
            lambda: Room.objects.get(id=self.room_id)
        )()

        members = await database_sync_to_async(
            lambda: list(room.members.exclude(id=self.user.id))
        )()

        for member in members:

            # 1. Save notification in database
            await self.save_chat_notification(
                member,
                room,
                message
            )

            # 2. Send real-time notification
            await self.channel_layer.group_send(
                f"user_{member.id}_notifications",
                {
                    "type": "send_notification",
                    "username": self.user.username,
                    "title": room.name,
                    "message": message.body,
                    "room_id": self.room_id,
                }
            )






