from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from rooms.models import Room


# ==========================================
# STUDY RESOURCES
# ==========================================

class Resource(models.Model):

    CATEGORY_CHOICES = [
        ("Python", "Python"),
        ("Django", "Django"),
        ("DSA", "DSA"),
        ("DBMS", "DBMS"),
        ("OS", "Operating System"),
        ("CN", "Computer Networks"),
        ("AI", "Artificial Intelligence"),
        ("Other", "Other"),
    ]

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    file = models.FileField(upload_to="resources/")

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    downloads = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ==========================================
# ASSIGNMENTS
# ==========================================

class Assignment(models.Model):

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="assignments"
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    assignment_file = models.FileField(
        upload_to="assignments/",
        blank=True,
        null=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    due_date = models.DateTimeField()

    total_marks = models.PositiveIntegerField(default=100)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_overdue(self):
        return timezone.now() > self.due_date

    def __str__(self):
        return self.title


# ==========================================
# STUDENT SUBMISSION
# ==========================================

class Submission(models.Model):

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions"
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    submitted_file = models.FileField(upload_to="submissions/")

    submitted_at = models.DateTimeField(auto_now_add=True)

    marks = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    feedback = models.TextField(blank=True)

    is_late = models.BooleanField(default=False)

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Submitted", "Submitted"),
        ("Late", "Late"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Submitted"
    )

    class Meta:
        unique_together = ("assignment", "student")

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"