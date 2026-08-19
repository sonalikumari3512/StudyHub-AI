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

]