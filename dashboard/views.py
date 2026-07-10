from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.models import UserProfile


@login_required
def dashboard(request):
    profile = UserProfile.objects.get(user=request.user)

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "profile": profile
        }
    )