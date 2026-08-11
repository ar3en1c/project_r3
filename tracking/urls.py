from django.urls import path
from . import views

app_name = "tracking"

urlpatterns = [
    path("series/<slug:slug>/status/", views.set_series_status, name="series_status"),
    path("series/<slug:slug>/progress/", views.set_series_progress, name="series_progress"),
    path("series/<slug:slug>/progress/increment/", views.increment_series_progress, name="series_progress_increment"),
    path("series/<slug:slug>/rating/", views.set_series_rating, name="series_rating"),
    path("series/<slug:slug>/favorite/", views.toggle_series_favorite, name="series_favorite"),
    path("movies/<slug:slug>/status/", views.set_movie_status, name="movie_status"),
    path("movies/<slug:slug>/rating/", views.set_movie_rating, name="movie_rating"),
    path("movies/<slug:slug>/favorite/", views.toggle_movie_favorite, name="movie_favorite"),
    path("favorites/", views.favorites_view, name="favorites"),
    path("favorite/remove/", views.remove_favorite, name="remove_favorite"),
]
