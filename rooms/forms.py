from django import forms
from .models import Room, Message


class RoomForm(forms.ModelForm):

    class Meta:
        model = Room
        fields = [
            "name",
            "description",
        ]


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["body"]
        widgets = {
            "body": forms.TextInput(
                attrs={
                    "placeholder": "Type your message...",
                    "class": "form-control"
                }
            )
        }

