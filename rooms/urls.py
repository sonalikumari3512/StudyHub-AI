from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.createRoom, name="create_room"),
    path("", views.rooms, name="rooms"),
    path("<int:pk>/", views.room_detail, name="room_detail"),
    path("<int:pk>/join/", views.join_room, name="join_room"),
    path("message/<int:pk>/delete/", views.delete_message, name="delete_message"),
    path("message/<int:pk>/edit/",views.edit_message,name="edit_message"),
    path("<int:pk>/leave/", views.leave_room, name="leave_room"),
    path(
    "room/<int:room_id>/messages/",views.room_messages, name="room_messages"),
    path(
    "<int:room_id>/announcement/create/",
    views.create_announcement,
    name="create_announcement",
    ),

    path(
        "announcement/<int:pk>/edit/",
        views.edit_announcement,
        name="edit_announcement",
    ),

    path(
        "announcement/<int:pk>/delete/",
        views.delete_announcement,
        name="delete_announcement",
    ),
]
