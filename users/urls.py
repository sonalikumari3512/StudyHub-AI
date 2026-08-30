from django.urls import path
from .import views

urlpatterns = [
    path('',views.home,name='home'),
    path("register/", views.register, name="register"),
    path("students/", views.students, name="students"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("edit-profile/",views.edit_profile,name="edit_profile"),
    path("notifications/", views.notifications, name="notifications"),
    path(
    "notifications/<int:notification_id>/read/",
    views.mark_notification_read,
    name="mark_notification_read"
    ),
    path(
    "notifications/read-all/",
    views.mark_all_notifications_read,
    name="mark_all_notifications_read"
   ),
]
