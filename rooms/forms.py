from django import forms
from .models import Room, Message,Announcement


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



class AnnouncementForm(forms.ModelForm):

    class Meta:

        model = Announcement

        fields = ["title", "content", "attachment"]

        widgets = {

            "title": forms.TextInput(attrs={
                "class":"form-control",
                "placeholder":"Announcement title"
            }),

            "content": forms.Textarea(attrs={
                "class":"form-control",
                "rows":5,
                "placeholder":"Write announcement..."
            }),

            "attachment": forms.ClearableFileInput(attrs={
                "class":"form-control"
            })

        }