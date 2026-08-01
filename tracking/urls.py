from django.urls import path
from . import views

app_name = "tracking"

urlpatterns = [
    path("series/<slug:slug>/status/", views.set_series_status, name="series_status"),
    path("series/<slug:slug>/progress/", views.set_series_progress, name="series_progress"),
    path("series/<slug:slug>/rating/", views.set_series_rating, name="series_rating"),
    path("movies/<slug:slug>/status/", views.set_movie_status, name="movie_status"),
    path("movies/<slug:slug>/rating/", views.set_movie_rating, name="movie_rating"),
]
