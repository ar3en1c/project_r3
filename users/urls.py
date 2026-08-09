from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("", views.profile_view, name="profile"),
    path("u/<int:user_id>/", views.public_profile_view, name="public_profile"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("series/<slug:slug>/stage/", views.series_stage, name="series_stage"),
    path("series/<slug:slug>/step/", views.series_step, name="series_step"),
    path("movies/<slug:slug>/stage/", views.movie_stage, name="movie_stage"),
    path("rate/", views.rate, name="rate"),
]
