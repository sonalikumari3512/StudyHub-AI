from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Task,PomodoroSession
from .forms import TaskForm



def get_pomodoro_stats(user):
    today = timezone.now().date()

    today_sessions = PomodoroSession.objects.filter(
        user=user,
        completed_at__date=today
    )

    focus_sessions_today = today_sessions.filter(session_type="focus")

    today_minutes = sum(
        s.duration_minutes for s in focus_sessions_today
    )

    session_count = focus_sessions_today.count()

    return today_minutes, session_count



@login_required
def task_list(request):

    tasks = Task.objects.filter(user=request.user)

    total = tasks.count()
    completed = tasks.filter(completed=True).count()
    pending = tasks.filter(completed=False).count()
    overdue = tasks.filter(
        completed=False,
        due_date__lt=timezone.now().date()
    ).count()

    progress = 0
    if total:
        progress = int((completed/total)*100)

    today_minutes, session_count = get_pomodoro_stats(request.user)

    return render(request, "tasks/task_list.html", {
        "tasks": tasks,
        "total": total,
        "completed": completed,
        "pending": pending,
        "overdue": overdue,
        "progress": progress,
        "today_minutes": today_minutes,
        "session_count": session_count,
    })

@login_required
def create_task(request):

    if request.method == "POST":

        form = TaskForm(request.POST)

        if form.is_valid():

            task = form.save(commit=False)
            task.user = request.user
            task.save()

            messages.success(request, "Task added successfully.")
            return redirect("task_list")

    else:
        form = TaskForm()

    return render(request, "tasks/task_form.html", {
        "form": form
    })


@login_required
def edit_task(request, pk):

    task = get_object_or_404(
        Task,
        pk=pk,
        user=request.user
    )

    if request.method == "POST":

        form = TaskForm(request.POST, instance=task)

        if form.is_valid():
            form.save()
            messages.success(request, "Task updated.")
            return redirect("task_list")

    else:
        form = TaskForm(instance=task)

    return render(request, "tasks/task_form.html", {
        "form": form,
        "edit": True
    })


@login_required
def toggle_task(request, pk):

    task = get_object_or_404(
        Task,
        pk=pk,
        user=request.user
    )

    task.completed = not task.completed
    task.save()

    return redirect("task_list")


@login_required
def delete_task(request, pk):

    task = get_object_or_404(
        Task,
        pk=pk,
        user=request.user
    )

    task.delete()

    messages.success(request, "Task deleted.")
    return redirect("task_list")


@login_required
def pomodoro_view(request):
    today_minutes, session_count = get_pomodoro_stats(request.user)

    return render(request, "tasks/pomodoro.html", {
        "today_minutes": today_minutes,
        "session_count": session_count,
    })


@login_required
@require_POST
def save_pomodoro_session(request):
    try:
        data = json.loads(request.body)
        session_type = data.get("session_type")
        duration_minutes = data.get("duration_minutes")

        if session_type not in ("focus", "short_break", "long_break"):
            return JsonResponse({"error": "Invalid session type"}, status=400)

        PomodoroSession.objects.create(
            user=request.user,
            session_type=session_type,
            duration_minutes=duration_minutes
        )

        today_minutes, session_count = get_pomodoro_stats(request.user)

        return JsonResponse({
            "success": True,
            "today_minutes": today_minutes,
            "session_count": session_count,
        })

    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"error": "Invalid data"}, status=400)