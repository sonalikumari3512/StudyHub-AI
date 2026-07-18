from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import RoomForm,MessageForm
from .models import Room,Message
from django.shortcuts import get_object_or_404,redirect

@login_required
def createRoom(request):

    form = RoomForm()

    if request.method == "POST":

        form = RoomForm(request.POST)

        if form.is_valid():

            room = form.save(commit=False)

            room.host = request.user

            room.save()

            return redirect("/dashboard/")

    context = {
        "form": form
    }

    return render(
        request,
        "rooms/create_room.html",
        context
    )


def rooms(request):
    rooms = Room.objects.all()

    return render(
        request,
        "rooms/rooms.html",
        {
            "rooms": rooms
        }
    )


def room_detail(request, pk):

    room = get_object_or_404(Room, id=pk)

    if request.method == "POST":

        form = MessageForm(request.POST)

        if form.is_valid():

            message = form.save(commit=False)

            message.room = room

            message.user = request.user

            message.save()

            return redirect("room_detail", pk=pk)

    else:

        form = MessageForm()

    return render(
        request,
        "rooms/room_detail.html",
        {
            "room": room,
            "form": form,
        }
    )


@login_required
def join_room(request, pk):

    room = get_object_or_404(Room, id=pk)

    room.members.add(request.user)

    return redirect("room_detail", pk=pk)