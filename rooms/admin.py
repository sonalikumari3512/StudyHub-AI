from django.contrib import admin
from .models import Room,Message,Topic,Notification

admin.site.register(Room)
admin.site.register(Message)
admin.site.register(Topic)
admin.site.register(Notification)