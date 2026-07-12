from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import RoomForm

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