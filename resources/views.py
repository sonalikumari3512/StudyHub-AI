from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from rooms.models import Room

from .models import Resource, Assignment, Submission
from .forms import ResourceForm, AssignmentForm, SubmissionForm

@login_required
def upload_resource(request):

    if request.method == "POST":

        form = ResourceForm(request.POST, request.FILES)

        if form.is_valid():

            resource = form.save(commit=False)

            resource.uploaded_by = request.user

            resource.save()

            return redirect("resource_list")

    else:

        form = ResourceForm()

    return render(
        request,
        "resources/upload_resource.html",
        {
            "form": form
        }
    )


@login_required
def resource_list(request):

    resources = Resource.objects.all().order_by("-created_at")

    search = request.GET.get("search", "").strip()

    category = request.GET.get("category", "").strip()

    if search:

        resources = resources.filter(
            title__icontains=search
        )

    if category:

        resources = resources.filter(
            category=category
        )

    categories = Resource.CATEGORY_CHOICES

    return render(
        request,
        "resources/resource_list.html",
        {
            "resources": resources,
            "categories": categories,
            "search": search,
            "selected_category": category,
        }
    )



@login_required
def download_resource(request, pk):

    resource = get_object_or_404(
        Resource,
        id=pk
    )

    resource.downloads += 1

    resource.save(
        update_fields=["downloads"]
    )

    return redirect(
        resource.file.url
    )

@login_required
def assignment_list(request, room_id):

    room = get_object_or_404(Room, id=room_id)

    assignments = room.assignments.all().order_by("-created_at")

    return render(
        request,
        "resources/assignment_list.html",
        {
            "room": room,
            "assignments": assignments,
        }
    )

@login_required
def create_assignment(request, room_id):

    room = get_object_or_404(Room, id=room_id)

    if request.user != room.host:
        messages.error(request, "Only room host can create assignments.")
        return redirect("assignment_list", room.id)

    if request.method == "POST":

        form = AssignmentForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            assignment = form.save(commit=False)

            assignment.room = room

            assignment.created_by = request.user

            assignment.save()
            messages.success(request, "Assignment created successfully!")
            return redirect(
                "assignment_list",
                room_id = room.id
            )

    else:
        form = AssignmentForm()

    return render(
        request,
        "resources/create_assignment.html",
        {
            "form": form,
            "room": room,
        }
    )

@login_required
def assignment_detail(request, pk):

    assignment = get_object_or_404(
        Assignment,
        id=pk
    )

    submission = Submission.objects.filter(
        assignment=assignment,
        student=request.user
    ).first()

    return render(
        request,
        "resources/assignment_detail.html",
        {
            "assignment": assignment,
            "submission": submission,
        }
    )


@login_required
def submit_assignment(request, assignment_id):

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id
    )

    # Host cannot submit
    if request.user == assignment.created_by:
        return redirect("assignment_detail", pk=assignment.id)

    # Prevent duplicate submission
    if Submission.objects.filter(
        assignment=assignment,
        student=request.user
    ).exists():
        return redirect("assignment_detail", pk=assignment.id)

    if request.method == "POST":

        form = SubmissionForm(request.POST, request.FILES)

        if form.is_valid():

            submission = form.save(commit=False)

            submission.assignment = assignment
            submission.student = request.user

            # Check late submission
            if timezone.now() > assignment.due_date:
                submission.is_late = True
                submission.status = "Late"
            else:
                submission.status = "Submitted"

            submission.save()

            return redirect("assignment_detail", pk=assignment.id)

    else:
        form = SubmissionForm()

    return render(
        request,
        "resources/submit_assignment.html",
        {
            "assignment": assignment,
            "form": form,
        }
    )


@login_required
def view_submissions(request, assignment_id):

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id
    )

    # Only room host can see submissions
    if request.user != assignment.created_by:
        return redirect("assignment_detail", pk=assignment.id)

    submissions = Submission.objects.filter(
        assignment=assignment
    ).select_related("student")

    return render(
        request,
        "resources/view_submissions.html",
        {
            "assignment": assignment,
            "submissions": submissions,
        }
    )