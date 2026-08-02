from django.shortcuts import render, get_object_or_404
import jdatetime

from .models import Person, Series
from tracking.models import Track

# Create your views here.


def _jalali_year():
    """Current Jalali year as Persian digits (e.g. ۱۴۰۵)."""
    year = jdatetime.datetime.now().year
    return str(year).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


# Map TVDB status strings to the tracking buttons' (value, label) tuples
STATUS_OPTIONS = [
    ("completed", "تکمیل شده"),
    ("watching", "در حال تماشا"),
    ("dropped", "رها شده"),
    ("plan to watch", "برنامه_تماشا"),
]


def series_list(request):
    series_list = Series.objects.all().order_by("-created_at")
    return render(request, "series/list.html", {"series_list": series_list})


def series(request, slug):
    obj = get_object_or_404(Series, slug=slug)

    characters = [
        {
            "name": c.character_name,
            "actor": c.person.name if c.person_id else "",
            "image": c.character_image or (c.person.image if c.person_id else ""),
            "person_tvdb": c.person.tvdb_id if c.person_id else "",
        }
        for c in obj.characters.select_related("person").all()
    ]

    imdb_id = next(
        (r.remote_id for r in obj.remote_ids.all() if r.source_name.lower() == "imdb"),
        "",
    )

    # Current user's tracking record for this series (if any)
    track = None
    if request.user.is_authenticated:
        track = Track.objects.filter(
            user=request.user, typeOfWatch="Series", serial=obj
        ).first()

    # Users' average rating (only tracks that actually have a rate)
    rates = list(
        Track.objects.filter(serial=obj, user_rate__isnull=False).values_list(
            "user_rate", flat=True
        )
    )
    avg_rate = round(sum(rates) / len(rates), 1) if rates else None

    contex = {
        # Hero
        "name": obj.name_fa or obj.name,
        "year": obj.year,
        "slug": obj.slug,
        "page_title_suffix": "جزئیات سریال",
        "genres": [g.genre.name for g in obj.series_genres.select_related("genre").all()],
        "poster_url": obj.image,
        "poster_alt": obj.name_fa or obj.name,

        # Status / progress
        "status": obj.status or "",
        "track_status": track.status if track else "",
        "favorite": track.favorite if track else False,
        "allEpisodes": obj.episode_count,
        "episodeWatched": (track.progress or 0) if track else 0,
        "score": int(track.user_rate or 0) if track else 0,

        # IMDb rating (from TVDB/IMDb import)
        "imdb_rate": obj.rate,

        # Users' average rating
        "avg_rate": avg_rate,

        # Status card (right column)
        "status_label": "تمام شده" if obj.status == "Ended" else "در حال پخش" if obj.status else "نامشخص",
        "total_seasons": obj.season_count,
        "total_units": obj.episode_count,

        # Metadata card
        "imdb_id": imdb_id,
        "language": obj.original_language,
        "country": obj.original_country,

        # Overview
        "overview": obj.overview or obj.overview_en,

        # Characters
        "characters": characters,

        # Status buttons
        "status_options": STATUS_OPTIONS,
    }
    return render(request, "series/index.html", contex)


def person(request, tvdb_id):
    """Person detail view."""
    obj = get_object_or_404(Person, tvdb_id=tvdb_id)

    characters = [
        {
            "name": c.character_name,
            "actor": c.person.name if c.person_id else "",
            "image": c.character_image or (c.person.image if c.person_id else ""),
        }
        for c in obj.characters.select_related("person").all()
    ]

    series_works = list(set(
        c.series for c in obj.characters.select_related("series").all()
    ))
    movie_works = list(set(
        c.movies for c in obj.movie_characters.select_related("movies").all()
    ))

    works = []
    for s in series_works:
        works.append({"type": "series", "item": s})
    for m in movie_works:
        works.append({"type": "movie", "item": m})
    works.sort(key=lambda w: w["item"].created_at, reverse=True)

    return render(request, "series/person.html", {
        "person": obj,
        "characters": characters,
        "works": works,
    })


def header(request):
    return render(request, "header.html")


def footer(request):
    return render(request, "footer.html", {
        "current_year": _jalali_year(),
    })

