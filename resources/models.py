from django.db import models
from django.contrib.auth.models import User


class Resource(models.Model):

    CATEGORY_CHOICES = [
        ("Python", "Python"),
        ("Django", "Django"),
        ("DSA", "DSA"),
        ("DBMS", "DBMS"),
        ("OS", "Operating System"),
        ("CN", "Computer Networks"),
        ("Other", "Other"),
    ]

    title = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    file = models.FileField(
        upload_to="resources/"
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    downloads = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title