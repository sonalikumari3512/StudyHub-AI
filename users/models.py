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