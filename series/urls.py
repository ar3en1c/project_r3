from django.urls import path
from . import views

app_name = "series"

urlpatterns = [
    path("", views.series_list, name="mainSeries"),
    path("header/", views.header, name="header"),
    path("footer/", views.footer, name="footer"),
    path("<slug:slug>/", views.series, name="series_detail"),
]
