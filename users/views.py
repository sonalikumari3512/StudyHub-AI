from django.shortcuts import render, redirect,get_object_or_404
from .models import UserProfile,Notification
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterUserForm, ProfileForm
from rooms.models import Room
from django.utils import timezone

def home(request):
    return render(request, "users/home.html")


def register(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")

    else:
        form = RegisterUserForm()

    return render(request, "users/register.html", {"form": form})





def login_user(request):
    if request.method == "POST":

        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():

            user = form.get_user()

            login(request, user)


            return redirect("/")

    else:

        form = AuthenticationForm()

    return render(
        request,
        "users/login.html",
        {
            "form": form
        }
    )


@login_required
def profile(request):

    profile = UserProfile.objects.get(user=request.user)

    created_rooms = Room.objects.filter(host=request.user)

    joined_rooms = request.user.joined_rooms.all()

    context = {
        "profile": profile,
        "created_rooms": created_rooms,
        "joined_rooms": joined_rooms,
    }

    return render(
        request,
        "users/profile.html",
        context,
    )


@login_required
def edit_profile(request):

    profile = UserProfile.objects.get(user=request.user)

    if request.method == "POST":

        form = ProfileForm(
            request.POST,
            instance=profile
        )

        if form.is_valid():

            form.save()

            return redirect("profile")

    else:

        form = ProfileForm(instance=profile)

    return render(
        request,
        "users/edit_profile.html",
        {
            "form": form
        }
    )


def logout_user(request):

    logout(request)

    return redirect("/")


def students(request):
    students = UserProfile.objects.all()

    return render(
        request,
        "users/students.html",
        {"students": students}
    )




@login_required
def notifications(request):
    notification_list = Notification.objects.filter(
        user=request.user
    )

    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return render(
        request,
        "users/notifications.html",
        {
            "notification_list": notification_list,
            "unread_count": unread_count,
        }
    )


@login_required
def mark_notification_read(request, notification_id):

    notification = Notification.objects.filter(
        id=notification_id,
        user=request.user
    ).first()

    if notification:
        notification.is_read = True
        notification.save()

    return redirect("notifications")


@login_required
def mark_all_notifications_read(request):

    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    return redirect("notifications")