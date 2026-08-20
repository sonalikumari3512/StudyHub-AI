from django.urls import path

from . import views


urlpatterns = [

    path(
        "upload/",
        views.upload_resource,
        name="upload_resource"
    ),
    path(
        "",
        views.resource_list,
        name="resource_list"
    ),
    path(
        "download/<int:pk>/",
        views.download_resource,
        name="download_resource"
    ),
     # Assignments
    path(
        "room/<int:room_id>/assignments/",
        views.assignment_list,
        name="assignment_list"
    ),

    path(
        "room/<int:room_id>/assignments/create/",
        views.create_assignment,
        name="create_assignment"
    ),

    path(
        "assignment/<int:pk>/",
        views.assignment_detail,
        name="assignment_detail"
    ),
    path(
        "assignment/<int:pk>/submit/",
        views.submit_assignment,
        name="submit_assignment"
    ),
]