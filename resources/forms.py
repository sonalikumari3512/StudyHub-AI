from django import forms
from .models import Resource, Assignment, Submission


# ===============================
# RESOURCE FORM
# ===============================

class ResourceForm(forms.ModelForm):

    class Meta:
        model = Resource

        fields = [
            "title",
            "description",
            "category",
            "file",
        ]

        widgets = {
            "title": forms.TextInput(attrs={"class":"form-control"}),
            "description": forms.Textarea(attrs={"class":"form-control","rows":4}),
            "category": forms.Select(attrs={"class":"form-select"}),
            "file": forms.ClearableFileInput(attrs={"class":"form-control"}),
        }


# ===============================
# ASSIGNMENT FORM
# ===============================

class AssignmentForm(forms.ModelForm):

    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                "type":"datetime-local",
                "class":"form-control"
            }
        )
    )

    class Meta:
        model = Assignment

        fields = [
            "title",
            "description",
            "assignment_file",
            "due_date",
            "total_marks",
        ]

        widgets = {
            "title": forms.TextInput(attrs={"class":"form-control","placeholder": "Enter assignment title"}),
            "description": forms.Textarea(attrs={"class":"form-control","rows":5,"placeholder": "Enter assignment instructions"}),
            "assignment_file": forms.ClearableFileInput(attrs={"class":"form-control"}),
            "total_marks": forms.NumberInput(attrs={"class":"form-control","placeholder": "100"}),
        }


# ===============================
# SUBMISSION FORM
# =========================

class SubmissionForm(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ["submitted_file"]

        widgets = {
            "submitted_file": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
        }