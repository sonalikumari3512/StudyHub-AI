from django import forms
from .models import Resource


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
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter resource title"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Describe this resource",
                    "rows": 4
                }
            ),

            "category": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "file": forms.ClearableFileInput(
                attrs={
                    "class": "form-control"
                }
            ),
        }