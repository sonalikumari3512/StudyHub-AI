from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from .models import Room,Message
from .forms import RoomForm, MessageForm


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

    return render(
        request,
        "rooms/create_room.html",
        {
            "form": form
        }
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


@login_required
def room_detail(request, pk):

    room = get_object_or_404(Room, id=pk)

    is_member = room.members.filter(id=request.user.id).exists()

    if request.method == "POST":

        if not is_member:
            return HttpResponseForbidden(
                "Join the room first."
            )

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
            "is_member": is_member,
        }
    )

@login_required
def join_room(request, pk):

    room = get_object_or_404(Room, id=pk)

    if request.user not in room.members.all():

        room.members.add(request.user)

    return redirect("room_detail", pk=pk)


@login_required
def delete_message(request, pk):

    message = get_object_or_404(Message, id=pk)

    if message.user != request.user:
        return HttpResponseForbidden("You cannot delete this message.")

    room_id = message.room.id

    message.delete()

    return redirect("room_detail", pk=room_id)