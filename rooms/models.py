from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    host = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=100)
    description = models.TextField()

    members = models.ManyToManyField(
        User,
        related_name="joined_rooms",
        blank=True
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Message(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    body = models.TextField()
    delivered = models.BooleanField(default=False)

    read = models.BooleanField(default=False)

    read_at = models.DateTimeField(
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.body[:50]


class Announcement(models.Model):

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="announcements"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=200)

    content = models.TextField()

    attachment = models.FileField(
        upload_to="announcements/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title