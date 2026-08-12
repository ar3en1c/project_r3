from collections import Counter

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from movies.models import Movies
from series.models import Series
from tracking.models import Track


@login_required
def home(request):
    # Continue-watching: series the user is watching, most recently updated first.
    continued = (
        Track.objects
        .filter(user=request.user, typeOfWatch="Series", status="watching", serial__isnull=False)
        .select_related("serial")
        .order_by("-updated_at")[:10]
    )
    # Plan-to-watch movies, best rated first (horizontal row).
    planned = (
        Track.objects
        .filter(user=request.user, typeOfWatch="Movie", status="plan to watch", movies__isnull=False)
        .select_related("movies")
        .order_by("-movies__rate")[:50]
    )
    # Plan-to-watch series, best rated first (horizontal row).
    planned_series = (
        Track.objects
        .filter(user=request.user, typeOfWatch="Series", status="plan to watch", serial__isnull=False)
        .select_related("serial")
        .order_by("-serial__rate")[:50]
    )
    # User's most-watched movie genre -> suggest top movies in it.
    genre_counts = Counter(
        g.genre.name for t in Track.objects.filter(
            user=request.user, typeOfWatch="Movie", movies__isnull=False,
        ).prefetch_related("movies__movie_genres__genre")
        for g in t.movies.movie_genres.all()
    )
    top_genre = genre_counts.most_common(1)[0][0] if genre_counts else ""
    suggested = []
    if top_genre:
        suggested = (
            Movies.objects.filter(
                movie_genres__genre__name=top_genre
            )
            .exclude(rate__isnull=True)
            .exclude(image="")
            .order_by("-year", "-rate")[:20]
        )

    # User's most-watched series genre -> suggest top series in it.
    sgenre_counts = Counter(
        g.genre.name for t in Track.objects.filter(
            user=request.user, typeOfWatch="Series", serial__isnull=False,
        ).prefetch_related("serial__series_genres__genre")
        for g in t.serial.series_genres.all()
    )
    top_sgenre = sgenre_counts.most_common(1)[0][0] if sgenre_counts else ""
    suggested_series = []
    if top_sgenre:
        suggested_series = (
            Series.objects.filter(
                series_genres__genre__name=top_sgenre
            )
            .exclude(rate__isnull=True)
            .exclude(image="")
            .order_by("-year", "-rate")[:20]
        )
    return render(request, "home/index.html", {
        "continued": continued,
        "planned": planned,
        "planned_series": planned_series,
        "suggested_genre": top_genre,
        "suggested": suggested,
        "suggested_sgenre": top_sgenre,
        "suggested_series": suggested_series,
    })