import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Room, Message


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"room_{self.room_id}"
        self.user = self.scope["user"]

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):

        print("🔥 MESSAGE RECEIVED:", text_data)

        data = json.loads(text_data)

        message = data["message"]

        saved_message = await self.save_message(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": saved_message.body,
                "username": saved_message.user.username,
                "time": saved_message.created_at.strftime("%d %b %Y, %I:%M %p"),
            }
        )

    async def chat_message(self, event):

        await self.send(
            text_data=json.dumps({
                "message": event["message"],
                "username": event["username"],
                "time": event["time"],
            })
        )

    @database_sync_to_async
    def save_message(self, body):

        room = Room.objects.get(id=self.room_id)

        return Message.objects.create(
            room=room,
            user=self.user,
            body=body,
        )