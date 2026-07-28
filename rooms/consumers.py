import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Message, Room


class ChatConsumer(AsyncWebsocketConsumer):

    # ==========================================
    # CONNECT
    # ==========================================

    async def connect(self):

        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"room_{self.room_id}"
        self.user = self.scope["user"]

        # Prevent anonymous users
        if self.user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    # ==========================================
    # DISCONNECT
    # ==========================================

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        # ==========================================
    # RECEIVE DATA
    # ==========================================

    async def receive(self, text_data):

        data = json.loads(text_data)

        event_type = data.get("type", "message")

        # -----------------------------
        # NEW MESSAGE
        # -----------------------------

        if event_type == "message":

            body = data.get("message", "").strip()

            if not body:
                return

            message = await self.create_message(body)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "id": message.id,
                    "message": message.body,
                    "username": message.user.username,
                    "user_id": message.user.id,
                    "time": message.created_at.strftime("%d %b %Y, %I:%M %p"),
                }
            )

        # -----------------------------
        # EDIT MESSAGE
        # -----------------------------

        elif event_type == "edit":

            message = await self.update_message(
                data.get("message_id"),
                data.get("message", "").strip(),
            )

            if message:

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "message_edited",
                        "id": message.id,
                        "message": message.body,
                    }
                )

        # -----------------------------
        # DELETE MESSAGE
        # -----------------------------

        elif event_type == "delete":

            deleted = await self.remove_message(
                data.get("message_id")
            )

            if deleted:

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "message_deleted",
                        "id": deleted,
                    }
                )

        # -----------------------------
        # USER TYPING
        # -----------------------------

        elif event_type == "typing":

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_status",
                    "username": self.user.username,
                    "typing": True,
                }
            )

        # -----------------------------
        # STOP TYPING
        # -----------------------------

        elif event_type == "stop_typing":

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_status",
                    "username": self.user.username,
                    "typing": False,
                }
            )



    # ==========================================
    # SEND NEW MESSAGE
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
                }
            )
        )



    # ==========================================
    # MESSAGE EDITED
    # ==========================================

    async def message_edited(self, event):

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

    async def message_deleted(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "type": "deleted",
                    "id": event["id"],
                }
            )
        )



    # ==========================================
    # TYPING STATUS
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
    # DATABASE METHODS
    # ==========================================

    @database_sync_to_async
    def create_message(self, body):

        room = Room.objects.get(id=self.room_id)

        return Message.objects.create(
            room=room,
            user=self.user,
            body=body
        )



    @database_sync_to_async
    def update_message(self, message_id, new_body):

        if not new_body:
            return None

        try:

            message = Message.objects.select_related(
                "user",
                "room"
            ).get(
                id=message_id,
                room_id=self.room_id
            )

        except Message.DoesNotExist:

            return None


        # Only the owner can edit
        if message.user_id != self.user.id:

            return None


        message.body = new_body
        message.save(update_fields=["body"])

        return message



    @database_sync_to_async
    def remove_message(self, message_id):

        try:

            message = Message.objects.get(
                id=message_id,
                room_id=self.room_id
            )

        except Message.DoesNotExist:

            return None


        # Only the owner can delete
        if message.user_id != self.user.id:

            return None


        deleted_id = message.id

        message.delete()

        return deleted_id