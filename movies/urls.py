"""Movie URLs."""
from django.urls import path
from . import views

urlpatterns = [
    path('<slug:slug>/', views.movie, name='movie_detail'),
]