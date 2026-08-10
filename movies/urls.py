"""Movie URLs."""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.movie_list, name='movie_list'),
    path('<slug:slug>/comment/', views.add_comment, name='movie_comment'),
    path('<slug:slug>/', views.movie, name='movie_detail'),
]