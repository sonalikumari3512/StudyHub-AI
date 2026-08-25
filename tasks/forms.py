from django import forms
from .models import Task

class TaskForm(forms.ModelForm):

    class Meta:

        model = Task

        fields = [
            "title",
            "description",
            "category",
            "priority",
            "due_date",
        ]

        widgets = {

            "title": forms.TextInput(attrs={
                "class":"form-control"
            }),

            "description": forms.Textarea(attrs={
                "class":"form-control",
                "rows":3
            }),

            "category": forms.Select(attrs={
                "class":"form-select"
            }),

            "priority": forms.Select(attrs={
                "class":"form-select"
            }),

            "due_date": forms.DateInput(attrs={
                "class":"form-control",
                "type":"date"
            }),

        }