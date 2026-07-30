from django import forms
from .models import Room, Message


class RoomForm(forms.ModelForm):

    class Meta:
        model = Room
        fields = [
            "topic",
            "name",
            "description",
        ]


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["body"]

        widgets = {
            "body": forms.Textarea(
                attrs={
                    "id": "message-input",
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Type your message..."
                }
            )
        }