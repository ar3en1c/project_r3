"""Global header search across series, movies, people and IMDb ids."""
from django.db.models import Q
from django.shortcuts import render

from series.models import Series, Person, RemoteId as SeriesRemoteId
from movies.models import Movies, RemoteId as MovieRemoteId

# ponytail: fixed per-group caps; fine for a dropdown. Add pagination if a group grows.
MAX_GROUP = 8
MAX_IMDB = 5


def search(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return render(request, "search/results.html", {
            "q": "", "series": [], "movies": [], "people": [], "imdb": [], "total": 0,
        })

    name_q = Q(name__icontains=q) | Q(name_fa__icontains=q) | Q(name_en__icontains=q)

    series = Series.objects.filter(name_q)[:MAX_GROUP]
    movies = Movies.objects.filter(name_q)[:MAX_GROUP]
    people = Person.objects.filter(name__icontains=q)[:MAX_GROUP]

    imdb = []
    for r in SeriesRemoteId.objects.filter(
        source_name__iexact="imdb", remote_id__icontains=q
    ).select_related("series")[:MAX_IMDB]:
        imdb.append({"remote_id": r.remote_id, "name": r.series.name_fa or r.series.name,
                     "year": r.series.year, "url_name": "series:series_detail",
                     "slug": r.series.slug, "type": "سریال"})
    for r in MovieRemoteId.objects.filter(
        source_name__iexact="imdb", remote_id__icontains=q
    ).select_related("movies")[:MAX_IMDB]:
        imdb.append({"remote_id": r.remote_id, "name": r.movies.name_fa or r.movies.name,
                     "year": r.movies.year, "url_name": "movie_detail",
                     "slug": r.movies.slug, "type": "فیلم"})

    series = list(series)
    movies = list(movies)
    people = list(people)
    total = len(series) + len(movies) + len(people) + len(imdb)

    return render(request, "search/results.html", {
        "q": q, "series": series, "movies": movies, "people": people,
        "imdb": imdb, "total": total,
    })
