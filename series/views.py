from datetime import date

from django.shortcuts import render, get_object_or_404
import jdatetime

from .models import Person, Series, Genre
from tracking.models import Track
from top250.rank import SERIES_RANKS


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

# Genres highlighted in the "top rated per genre" section.
TOP_GENRES = ["drama", "action", "comedy"]

# Countries highlighted in the "top rated per country" section.
TOP_COUNTRIES = [("usa", "آمریکا"), ("irn", "ایران"), ("kor", "کره جنوبی")]

# Famous actors (DB-safe: only names actually present in the Person table).
FAMOUS_ACTORS = [
    "Leonardo DiCaprio",
    "Brad Pitt",
    "Tom Hanks",
    "Robert De Niro",
    "Scarlett Johansson",
    "Mehran Modiri",
    "Behrouz Vossoughi"
]


def series_list(request):
    """Series homepage: hero carousel + genre/country top rows + famous actors."""
    current_year = str(date.today().year)

    # 1) Hero: rated above 8, best first.
    hero = Series.objects.filter(rate__gt=8).exclude(image="").order_by("-rate")[:8]

    # 2) Genres list.
    genres = Genre.objects.all().order_by("name")

    # 3) Top rated per selected genre.
    top_genres = []
    for name in TOP_GENRES:
        genre = Genre.objects.filter(name__iexact=name).first()
        if genre is None:
            continue
        series_qs = (
            Series.objects.filter(series_genres__genre=genre)
            .exclude(image="")
            .exclude(rate__isnull=True)
            .order_by("-rate")[:8]
        )
        top_genres.append({"name": genre.name, "slug": genre.slug, "series": series_qs})

    # 4) Top rated per selected country.
    top_countries = []
    for code, label in TOP_COUNTRIES:
        series_qs = (
            Series.objects.filter(original_country=code)
            .exclude(image="")
            .exclude(rate__isnull=True)
            .order_by("-rate")[:8]
        )
        top_countries.append({"code": code, "label": label, "series": series_qs})

    # 5) Famous actors (skip any name not present in the DB).
    actors = []
    for name in FAMOUS_ACTORS:
        person = Person.objects.filter(name__iexact=name).first()
        if person is not None:
            actors.append({"tvdb_id": person.tvdb_id, "name": person.name, "image": person.image})

    return render(request, "series/list.html", {
        "current_year": current_year,
        "hero": hero,
        "genres": genres,
        "top_genres": top_genres,
        "top_countries": top_countries,
        "actors": actors,
    })


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
        "top250_rank": SERIES_RANKS.get(imdb_id),
        "language": obj.original_language,
        "country": obj.original_country,

        # Overview
        "overview": obj.overview or obj.overview_en,

        # Characters
        "characters": characters,

        # Status buttons
        "status_options": STATUS_OPTIONS,

        # Watch on Filimo / Namava
        "filimo": obj.filimo or "",
        "namava": obj.namava or "",
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

    # Per-work tracking status for the current user
    for w in works:
        w["status"] = None
    if request.user.is_authenticated and works:
        series_ids = [w["item"].id for w in works if w["type"] == "series"]
        movie_ids = [w["item"].id for w in works if w["type"] == "movie"]
        series_status = dict(
            Track.objects.filter(
                user=request.user, typeOfWatch="Series", serial_id__in=series_ids
            ).values_list("serial_id", "status")
        )
        movie_status = dict(
            Track.objects.filter(
                user=request.user, typeOfWatch="Movie", movies_id__in=movie_ids
            ).values_list("movies_id", "status")
        )
        for w in works:
            w["status"] = (
                series_status.get(w["item"].id)
                if w["type"] == "series"
                else movie_status.get(w["item"].id)
            )

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

