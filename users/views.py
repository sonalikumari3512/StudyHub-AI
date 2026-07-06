from django.shortcuts import render, redirect
from .forms import UserProfileForm
from django.contrib import messages
from .models import UserProfile

def home(request):
    return render(request, "users/home.html")


def register(request):

    if request.method == "POST":
        form = UserProfileForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Registration Successful!")
            return redirect("register")

    else:
        form = UserProfileForm()

    return render(request, "users/register.html", {"form": form})

def students(request):
    students = UserProfile.objects.all()

    return render(
        request,
        "users/students.html",
        {"students": students}
    )