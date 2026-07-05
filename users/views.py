from django.shortcuts import render, redirect
from .forms import UserProfileForm

def home(request):
    return render(request, "users/home.html")


def register(request):

    if request.method == "POST":
        form = UserProfileForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("/") 

    else:
        form = UserProfileForm()

    return render(request, "users/register.html", {"form": form})