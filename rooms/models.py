from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
    host = models.ForeignKey(
        User,
        on_delete=models.CASCADE
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



class Message(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE
    )

    body = models.TextField()

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.body[:30]