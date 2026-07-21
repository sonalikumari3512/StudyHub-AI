from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.createRoom, name="create_room"),
    path("", views.rooms, name="rooms"),
    path("<int:pk>/", views.room_detail, name="room_detail"),
    path("<int:pk>/join/", views.join_room, name="join_room"),
    path("message/<int:pk>/delete/", views.delete_message, name="delete_message"),
]
