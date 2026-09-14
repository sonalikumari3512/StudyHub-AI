from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Task(models.Model):

    PRIORITY_CHOICES = [
        ("High", "High"),
        ("Medium", "Medium"),
        ("Low", "Low"),
    ]

    CATEGORY_CHOICES = [
        ("DSA", "DSA"),
        ("DBMS", "DBMS"),
        ("OS", "OS"),
        ("CN", "CN"),
        ("ML", "Machine Learning"),
        ("Django", "Django"),
        ("Placement", "Placement"),
        ("Other", "Other"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="Other"
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="Medium"
    )

    due_date = models.DateField()

    completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["completed", "due_date"]

    @property
    def is_overdue(self):
        return not self.completed and self.due_date < timezone.now().date()

    def __str__(self):
        return self.title


class PomodoroSession(models.Model):

    SESSION_TYPE_CHOICES = [
        ("focus", "Focus"),
        ("short_break", "Short Break"),
        ("long_break", "Long Break"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="pomodoro_sessions"
    )

    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPE_CHOICES
    )

    duration_minutes = models.PositiveIntegerField()

    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]

    def __str__(self):
        return f"{self.user.username} - {self.session_type} ({self.duration_minutes} min)"