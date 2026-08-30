from .models import Notification

def notification_count(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by("-created_at")

        return {
            "unread_notification_count": unread_notifications.count(),
            "recent_notifications": unread_notifications[:5],   # Latest 5
        }

    return {
        "unread_notification_count": 0,
        "recent_notifications": [],
    }