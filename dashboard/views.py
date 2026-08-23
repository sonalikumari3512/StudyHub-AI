from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from users.models import UserProfile
from rooms.models import Room
from resources.models import Resource, Assignment, Submission


@login_required
def dashboard(request):

    user = request.user

    # Existing profile (keep this)
    profile = UserProfile.objects.get(user=user)

   # Rooms joined by current user
    joined_rooms = Room.objects.filter(members=user)

    # Resources uploaded by current user
    uploaded_resources = Resource.objects.filter(
        uploaded_by=user
    ).order_by("-created_at")

    # Assignments submitted by current user
    submitted_assignments = Submission.objects.filter(
        student=user
    ).select_related("assignment", "assignment__room").order_by("-submitted_at")

    # Upcoming assignments from joined rooms
    upcoming_assignments = Assignment.objects.filter(
        room__members=user,
        due_date__gte=timezone.now()
    ).select_related("room").order_by("due_date")[:5]

    # Recent uploads
    recent_resources = uploaded_resources[:5]

    # Recent submissions
    recent_submissions = submitted_assignments[:5]

    # Upcoming assignments for rooms user joined
    upcoming_assignments = Assignment.objects.filter(
        room__members=user,
        due_date__gte=timezone.now()
    ).order_by("due_date")[:5]

    # Recent activity
    recent_resources = uploaded_resources.order_by("-created_at")[:5]
    recent_submissions = submitted_assignments.order_by("-submitted_at")[:5]

    # Statistics
    total_assignments = Assignment.objects.filter(room__members=user).count()
    submitted_count = submitted_assignments.count()
    pending_count = max(total_assignments - submitted_count, 0)

    progress = 0
    if total_assignments > 0:
        progress = int((submitted_count / total_assignments) * 100)

    context = {
        "profile": profile,  # Keep profile for existing HTML

        # Analytics
        "rooms_count": joined_rooms.count(),
        "resources_count": uploaded_resources.count(),
        "submitted_count": submitted_count,
        "pending_count": pending_count,
        "progress": progress,

        # Lists
        "upcoming_assignments": upcoming_assignments,
        "recent_resources": recent_resources,
        "recent_submissions": recent_submissions,
    }

    return render(request, "dashboard/dashboard.html", context)