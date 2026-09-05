from django.urls import path

from .consumers import ChatConsumer

from .notification_consumer import NotificationConsumer
from .video_consumer import VideoConsumer

websocket_urlpatterns = [


    path(

        "ws/rooms/<int:room_id>/",

        ChatConsumer.as_asgi()

    ),
     path(
        "ws/notifications/",
        NotificationConsumer.as_asgi()
    ),

    path(
        "ws/video/<int:room_id>/",
        VideoConsumer.as_asgi()
    ),

]