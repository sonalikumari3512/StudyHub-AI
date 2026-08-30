import json

from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]

        # Don't allow anonymous users
        if not self.user.is_authenticated:
            await self.close()
            return

        # Each user gets their own notification group
        self.notification_group_name = (
            f"user_{self.user.id}_notifications"
        )

        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):

        if hasattr(self, "notification_group_name"):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )

    async def send_notification(self, event):

        await self.send(
            text_data=json.dumps({
                "type": "notification",
                "username": event.get("username"),
                "title": event.get("title"),
                "message": event.get("message"),
                "room_id": event.get("room_id"),
            })
        )