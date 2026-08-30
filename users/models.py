from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    college = models.CharField(max_length=100)

    year = models.IntegerField()

    branch = models.CharField(max_length=100)

    # ------------------------
    # Online Status
    # ------------------------
    is_online = models.BooleanField(
        default=False
    )

    last_seen = models.DateTimeField(
        default=timezone.now
    )

    def __str__(self):
        return self.user.username


# Existing UserProfile model stays above...


class Notification(models.Model):

    NOTIFICATION_TYPES = [
        ("assignment", "Assignment"),
        ("resource", "Resource"),
        ("chat", "Chat"),
        ("task", "Task"),
        ("grade", "Grade"),
        ("room", "Room"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=150)

    message = models.TextField()

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )

    link = models.CharField(
        max_length=255,
        blank=True
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"