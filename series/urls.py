from django.urls import path
from . import views

app_name = "series"

urlpatterns = [
    path("", views.series, name="mainSeries"),
    path("header/", views.header, name="header"),
    path("footer/", views.footer, name="footer"),
]
