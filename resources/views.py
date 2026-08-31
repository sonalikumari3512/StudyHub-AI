from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.http import FileResponse, Http404

from django.contrib.auth.models import User
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from rooms.models import Room
from users.models import Notification

from .models import Resource, Assignment, Submission
from .forms import (
    ResourceForm,
    AssignmentForm,
    SubmissionForm,
    GradeSubmissionForm,
)


@login_required
def upload_resource(request):
    if request.method == "POST":
        form = ResourceForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.save()

            # ==========================================
            # RESOURCE NOTIFICATIONS
            # ==========================================

            # Notify all users except uploader
            members = User.objects.exclude(
                id=request.user.id
            )

            channel_layer = get_channel_layer()

            for member in members:

                # 1️⃣ Save notification in database
                Notification.objects.create(
                    user=member,
                    title="📁 New Resource",
                    message=f"{request.user.username} uploaded '{resource.title}'.",
                    notification_type="resource",
                    link="/resources/",
                )

                # 2️⃣ Send real-time notification
                async_to_sync(
                    channel_layer.group_send
                )(
                    f"user_{member.id}_notifications",
                    {
                        "type": "send_notification",
                        "username": request.user.username,
                        "title": "📁 New Resource",
                        "message": f"{request.user.username} uploaded '{resource.title}'.",
                    }
                )

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

    # Check if file exists
    if not resource.file:
        raise Http404("File not found.")

    # Increase download count
    resource.downloads += 1
    resource.save(update_fields=["downloads"])

    # Force file download
    response = FileResponse(
        resource.file.open("rb"),
        as_attachment=True,
        filename=resource.file.name.split("/")[-1]
    )

    return response


@login_required
def preview_resource(request, pk):
    resource = get_object_or_404(
        Resource,
        id=pk
    )

    if not resource.file:
        messages.error(
            request,
            "No file available for preview."
        )
        return redirect("resource_list")

    file_name = resource.file.name.lower()

    # PDF
    if file_name.endswith(".pdf"):
        file_type = "pdf"

    # Images
    elif file_name.endswith(
        (".jpg", ".jpeg", ".png", ".gif", ".webp")
    ):
        file_type = "image"

    # Text
    elif file_name.endswith(".txt"):
        file_type = "text"

    # Unsupported
    else:
        file_type = "unsupported"

    return render(
        request,
        "resources/file_preview.html",
        {
            "resource": resource,
            "file_type": file_type,
            "file_url": resource.file.url,
        }
    )


@login_required
def assignment_list(request, room_id):
    room = get_object_or_404(
        Room,
        id=room_id
    )

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
    room = get_object_or_404(
        Room,
        id=room_id
    )

    if request.user != room.host:
        messages.error(
            request,
            "Only room host can create assignments."
        )
        return redirect(
            "assignment_list",
            room.id
        )

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

            # ==========================================
            # ASSIGNMENT NOTIFICATIONS
            # ==========================================

            members = room.members.exclude(
                id=request.user.id
            )

            channel_layer = get_channel_layer()

            for member in members:

                # 1️⃣ Save notification in database
                Notification.objects.create(
                    user=member,
                    title="📚 New Assignment",
                    message=f"{request.user.username} posted '{assignment.title}' in {room.name}.",
                    notification_type="assignment",
                    link=f"/rooms/{room.id}/assignments/",
                )

                # 2️⃣ Send real-time notification
                async_to_sync(
                    channel_layer.group_send
                )(
                    f"user_{member.id}_notifications",
                    {
                        "type": "send_notification",
                        "username": request.user.username,
                        "title": "📚 New Assignment",
                        "message": f"{request.user.username} posted '{assignment.title}' in {room.name}.",
                        "room_id": room.id,
                    }
                )

            messages.success(
                request,
                "Assignment created successfully!"
            )

            return redirect(
                "assignment_list",
                room_id=room.id
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
def preview_assignment_file(request, pk):
    assignment = get_object_or_404(
        Assignment,
        id=pk
    )

    if not assignment.assignment_file:
        messages.error(
            request,
            "No file available for preview."
        )
        return redirect(
            "assignment_detail",
            pk=assignment.id
        )

    file_name = assignment.assignment_file.name.lower()

    if file_name.endswith(".pdf"):
        file_type = "pdf"

    elif file_name.endswith(
        (".jpg", ".jpeg", ".png", ".gif", ".webp")
    ):
        file_type = "image"

    elif file_name.endswith(".txt"):
        file_type = "text"

    else:
        file_type = "unsupported"

    return render(
        request,
        "resources/assignment_file_preview.html",
        {
            "assignment": assignment,
            "file_type": file_type,
            "file_url": assignment.assignment_file.url,
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
        return redirect(
            "assignment_detail",
            pk=assignment.id
        )

    # Prevent duplicate submission
    if Submission.objects.filter(
        assignment=assignment,
        student=request.user
    ).exists():
        return redirect(
            "assignment_detail",
            pk=assignment.id
        )

    if request.method == "POST":
        form = SubmissionForm(
            request.POST,
            request.FILES
        )

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

            return redirect(
                "assignment_detail",
                pk=assignment.id
            )

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
        return redirect(
            "assignment_detail",
            pk=assignment.id
        )

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


@login_required
def grade_submission(request, submission_id):
    submission = get_object_or_404(
        Submission,
        id=submission_id
    )

    room = submission.assignment.room

    # ==========================================
    # ONLY HOST CAN GRADE
    # ==========================================

    if request.user != room.host:
        messages.error(
            request,
            "Only host can grade submissions."
        )

        return redirect(
            "assignment_detail",
            submission.assignment.id
        )

    if request.method == "POST":
        form = GradeSubmissionForm(
            request.POST,
            instance=submission
        )

        if form.is_valid():

            # ==========================================
            # SAVE GRADE
            # ==========================================

            graded = form.save(commit=False)
            graded.status = "Graded"
            graded.save()

            # ==========================================
            # ⭐ ASSIGNMENT GRADED NOTIFICATION
            # ==========================================

            student = submission.student
            assignment = submission.assignment

            notification_message = (
                f"{request.user.username} graded your "
                f"assignment '{assignment.title}' "
                f"in {room.name}."
            )

            # 1️⃣ Save notification in database
            Notification.objects.create(
                user=student,
                title="⭐ Assignment Graded",
                message=notification_message,
                notification_type="grade",
                link=f"/rooms/{room.id}/assignments/",
            )

            # 2️⃣ Send real-time notification
            channel_layer = get_channel_layer()

            async_to_sync(
                channel_layer.group_send
            )(
                f"user_{student.id}_notifications",
                {
                    "type": "send_notification",
                    "username": request.user.username,
                    "title": "⭐ Assignment Graded",
                    "message": notification_message,
                    "room_id": room.id,
                }
            )

            messages.success(
                request,
                "Submission graded successfully."
            )

            return redirect(
                "view_submissions",
                submission.assignment.id
            )

    else:
        form = GradeSubmissionForm(
            instance=submission
        )

    return render(
        request,
        "resources/grade_submission.html",
        {
            "submission": submission,
            "form": form,
        }
    )


@login_required
def preview_submission_file(request, pk):
    submission = get_object_or_404(
        Submission,
        id=pk
    )

    # Only the student who submitted or the room host can preview it
    if (
        request.user != submission.student
        and request.user != submission.assignment.created_by
    ):
        messages.error(
            request,
            "You don't have permission to preview this file."
        )

        return redirect(
            "assignment_detail",
            pk=submission.assignment.id
        )

    if not submission.submitted_file:
        messages.error(
            request,
            "No submission file available."
        )

        return redirect(
            "assignment_detail",
            pk=submission.assignment.id
        )

    file_name = submission.submitted_file.name.lower()

    if file_name.endswith(".pdf"):
        file_type = "pdf"

    elif file_name.endswith(
        (".jpg", ".jpeg", ".png", ".gif", ".webp")
    ):
        file_type = "image"

    elif file_name.endswith(".txt"):
        file_type = "text"

    else:
        file_type = "unsupported"

    return render(
        request,
        "resources/file_preview.html",
        {
            "resource": submission,
            "file_type": file_type,
            "is_submission": True,
            "file_url": submission.submitted_file.url,
        },
    )

