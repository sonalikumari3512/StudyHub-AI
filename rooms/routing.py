from django.urls import path

from .consumers import ChatConsumer
from .notification_consumer import NotificationConsumer



websocket_urlpatterns = [


    path(

        "ws/rooms/<int:room_id>/",

        ChatConsumer.as_asgi()

    ),



    path(

        "ws/notifications/",

        NotificationConsumer.as_asgi()

    ),


]