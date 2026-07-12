from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.createRoom, name="create_room"),
]
