from django.urls import path
from .import views

urlpatterns = [
    path('',views.home,name='home'),
    path("register/", views.register, name="register"),
    path("students/", views.students, name="students"),
]
