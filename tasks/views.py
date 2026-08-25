from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import Task
from .forms import TaskForm


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

    return render(request, "tasks/task_list.html", {
        "tasks": tasks,
        "total": total,
        "completed": completed,
        "pending": pending,
        "overdue": overdue,
        "progress": progress,
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
