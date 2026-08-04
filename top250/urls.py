from django.urls import path

from . import views

app_name = "top250"

urlpatterns = [
    path("", views.top250_view, name="top250"),
]
