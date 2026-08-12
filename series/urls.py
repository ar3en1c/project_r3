from django.urls import path
from . import views

app_name = "series"

urlpatterns = [
    path("", views.series_list, name="mainSeries"),
    path("filter/", views.series_filter, name="series_filter"),
    path("header/", views.header, name="header"),
    path("footer/", views.footer, name="footer"),
    path("<slug:slug>/comment/", views.add_comment, name="series_comment"),
    path("<slug:slug>/", views.series, name="series_detail"),
    path("person/<int:tvdb_id>/", views.person, name="person_detail"),
]
