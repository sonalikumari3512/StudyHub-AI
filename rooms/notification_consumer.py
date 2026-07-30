import json

from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):


    async def connect(self):

        self.user = self.scope["user"]


        if self.user.is_anonymous:

            await self.close()

            return



        self.notification_group_name = (
            f"user_{self.user.id}_notifications"
        )


        await self.channel_layer.group_add(

            self.notification_group_name,

            self.channel_name

        )


        await self.accept()



    async def disconnect(self, close_code):


        await self.channel_layer.group_discard(

            self.notification_group_name,

            self.channel_name

        )



    async def send_notification(self, event):

        print("NOTIFICATION EVENT:", event)
        await self.send(

            text_data=json.dumps(

                {

                    "type":"notification",

                    "username":
                    event["username"],


                    "message":
                    event["message"],


                    "room_id":
                    event["room_id"],

                }

            )

        )