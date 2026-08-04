import csv
from pathlib import Path

from django.shortcuts import render

from movies.models import Movies
from series.models import Series

BASE_DIR = Path(__file__).resolve().parent.parent
MOVIES_CSV = BASE_DIR / "datas" / "imdb_movies_top250.csv"
SERIES_CSV = BASE_DIR / "datas" / "imdb_series_top250.csv"


def _read_ids(path):
    with open(path, encoding="utf-8") as f:
        return [row["id"] for row in csv.DictReader(f)]


def top250_view(request):
    def ranked(qs, ids):
        found = {
            r.remote_id: obj
            for obj in qs.filter(
                remote_ids__source_name__iexact="imdb", remote_ids__remote_id__in=ids
            ).prefetch_related("remote_ids")
            for r in obj.remote_ids.all()
            if r.source_name.lower() == "imdb"
        }
        return [
            {"rank": i, "item": found[imdb_id]}
            for i, imdb_id in enumerate(ids, 1)
            if imdb_id in found
        ]

    movies = ranked(Movies.objects.all(), _read_ids(MOVIES_CSV))
    series = ranked(Series.objects.all(), _read_ids(SERIES_CSV))

    return render(request, "top250/index.html", {"movies": movies, "series": series})
