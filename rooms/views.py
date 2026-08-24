from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden,JsonResponse

from .models import Room,Message,Topic,Announcement
from .forms import RoomForm, MessageForm,AnnouncementForm
from django.db.models import Q
from django.contrib import messages


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

    query = request.GET.get("q", "")
    topic_id = request.GET.get("topic")

    topics = Topic.objects.all()

    rooms = Room.objects.all()

    if topic_id:
        rooms = rooms.filter(topic_id=topic_id)

    if query:
        rooms = rooms.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(host__username__icontains=query)
        )

    rooms = rooms.order_by("-created")

    return render(
        request,
        "rooms/rooms.html",
        {
            "rooms": rooms,
            "topics": topics,
            "query": query,
        }
    )


@login_required
def room_detail(request, pk):

    room = get_object_or_404(Room, id=pk)

    is_member = room.members.filter(id=request.user.id).exists()

    form = MessageForm()

    announcements = room.announcements.all()
    return render(
        request,
        "rooms/room_detail.html",
        {
            "room": room,
            "form": form,
            "is_member": is_member,
            "announcements": announcements,
        }
    )


@login_required
def join_room(request, pk):

    room = get_object_or_404(Room, id=pk)

    if request.method == "POST":

        if not room.members.filter(id=request.user.id).exists():
            room.members.add(request.user)

    return redirect("room_detail", pk=pk)


@login_required
def delete_message(request, pk):

    message = get_object_or_404(Message, id=pk)

    if message.user != request.user:
        return HttpResponseForbidden(
            "You cannot delete this message."
        )

    if request.method == "POST":

        room_id = message.room.id

        message.delete()

        return redirect("room_detail", pk=room_id)

    return render(
        request,
        "rooms/delete_message.html",
        {
            "message": message
        }
    )

@login_required
def edit_message(request, pk):

    message = get_object_or_404(Message, id=pk)

    if message.user != request.user:
        return HttpResponseForbidden(
            "You cannot edit this message."
        )

    if request.method == "POST":

        form = MessageForm(
            request.POST,
            instance=message
        )

        if form.is_valid():
            form.save()

            return redirect(
                "room_detail",
                pk=message.room.id
            )

    else:

        form = MessageForm(instance=message)

    return render(
        request,
        "rooms/edit_message.html",
        {
            "form": form
        }
    )

@login_required
def leave_room(request, pk):

    room = get_object_or_404(Room, id=pk)

    if request.method == "POST":

        room.members.remove(request.user)

    return redirect("rooms")



def room_messages(request, room_id):

    room = get_object_or_404(Room, id=room_id)

    messages = []

    for message in room.messages.all():

        messages.append({
            "user": message.user.username,
            "body": message.body,
            "time": message.created_at.strftime("%d %b %Y, %I:%M %p"),
        })

    return JsonResponse(messages, safe=False)

@login_required
def create_announcement(request, room_id):

    room = get_object_or_404(Room, id=room_id)

    if request.user != room.host:
        messages.error(request, "Only host can create announcements.")
        return redirect("room_detail", room.id)

    if request.method == "POST":

        form = AnnouncementForm(request.POST, request.FILES)

        if form.is_valid():

            announcement = form.save(commit=False)

            announcement.room = room
            announcement.author = request.user

            announcement.save()

            messages.success(request, "Announcement posted successfully.")

            return redirect("room_detail", room.id)

    else:

        form = AnnouncementForm()

    return render(
        request,
        "rooms/create_announcement.html",
        {
            "room": room,
            "form": form,
        },
    )

@login_required
def edit_announcement(request, pk):

    announcement = get_object_or_404(Announcement, id=pk)

    if request.user != announcement.room.host:
        messages.error(request, "Only host can edit.")
        return redirect("room_detail", announcement.room.id)

    if request.method == "POST":

        form = AnnouncementForm(
            request.POST,
            request.FILES,
            instance=announcement,
        )

        if form.is_valid():

            form.save()

            messages.success(request, "Announcement updated.")

            return redirect("room_detail", announcement.room.id)

    else:

        form = AnnouncementForm(instance=announcement)

    return render(
        request,
        "rooms/create_announcement.html",
        {
            "room": announcement.room,
            "form": form,
            "edit": True,
        },
    )

@login_required
def delete_announcement(request, pk):

    announcement = get_object_or_404(Announcement, id=pk)

    room = announcement.room

    if request.user != room.host:
        messages.error(request, "Only host can delete.")
        return redirect("room_detail", room.id)

    announcement.delete()

    messages.success(request, "Announcement deleted.")

    return redirect("room_detail", room.id)