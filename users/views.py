from django.shortcuts import render, redirect
from .models import UserProfile
from .forms import RegisterUserForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

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

    return render(request, "users/login.html", {"form": form})



@login_required
def profile(request):
    profile = UserProfile.objects.get(user=request.user)

    return render(
        request,
        "users/profile.html",
        {
            "profile": profile
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