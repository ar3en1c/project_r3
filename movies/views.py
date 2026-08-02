"""Movie views."""
from datetime import date

from django.shortcuts import render, get_object_or_404
import jdatetime

from .models import Movies
from series.models import Genre, Person
from tracking.models import Track


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


def movie(request, slug):
    """Movie detail view."""
    obj = get_object_or_404(Movies, slug=slug)

    characters = [
        {
            "name": c.character_name,
            "actor": c.person.name if c.person_id else "",
            "image": c.character_image or (c.person.image if c.person_id else ""),
            "person_tvdb": c.person.tvdb_id if c.person_id else "",
        }
        for c in obj.characters.select_related("person").filter(people_type="Actor")
    ]

    imdb_id = next(
        (r.remote_id for r in obj.remote_ids.all() if r.source_name.lower() == "imdb"),
        "",
    )

    # Get genres
    genres = [g.genre.name for g in obj.movie_genres.select_related("genre").all()]

    # Current user's tracking record for this movie (if any)
    track = None
    if request.user.is_authenticated:
        track = Track.objects.filter(
            user=request.user, typeOfWatch="Movie", movies=obj
        ).first()

    # Users' average rating (only tracks that actually have a rate)
    rates = list(
        Track.objects.filter(movies=obj, user_rate__isnull=False).values_list(
            "user_rate", flat=True
        )
    )
    avg_rate = round(sum(rates) / len(rates), 1) if rates else None

    context = {
        # Hero
        "name": obj.name_fa or obj.name,
        "year": obj.year,
        "slug": obj.slug,
        "page_title_suffix": "جزئیات فیلم",
        "genres": genres,
        "poster_url": obj.image,
        "poster_alt": obj.name_fa or obj.name,

        # Status / progress
        "status": obj.status or "",
        "track_status": track.status if track else "",
        "favorite": track.favorite if track else False,
        "score": int(track.user_rate or 0) if track else 0,

        # IMDb rating (from TVDB/IMDb import)
        "imdb_rate": obj.rate,

        # Users' average rating
        "avg_rate": avg_rate,

        # Status card (right column)
        "status_label": "تمام شده" if obj.status == "Released" else "در حال پخش" if obj.status else "نامشخص",

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
    return render(request, "movies/index.html", context)


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


def movie_list(request):
    """Movies homepage: hero carousel + genre/country top rows + famous actors."""
    current_year = str(date.today().year)

    # 1) Hero: this year, rated above 8, best first.
    hero = Movies.objects.filter(year__gt=2020, rate__gt=8).exclude(image="").order_by("-rate")[:8]

    # 2) Genres list.
    genres = Genre.objects.all().order_by("name")

    # 3) Top rated per selected genre.
    top_genres = []
    for name in TOP_GENRES:
        genre = Genre.objects.filter(name__iexact=name).first()
        if genre is None:
            continue
        movies = (
            Movies.objects.filter(movie_genres__genre=genre)
            .exclude(image="")
            .exclude(rate__isnull=True)
            .order_by("-rate")[:8]
        )
        top_genres.append({"name": genre.name, "slug": genre.slug, "movies": movies})

    # 4) Top rated per selected country.
    top_countries = []
    for code, label in TOP_COUNTRIES:
        movies = (
            Movies.objects.filter(original_country=code)
            .exclude(image="")
            .exclude(rate__isnull=True)
            .order_by("-rate")[:8]
        )
        top_countries.append({"code": code, "label": label, "movies": movies})

    # 5) Famous actors (skip any name not present in the DB).
    actors = []
    for name in FAMOUS_ACTORS:
        person = Person.objects.filter(name__iexact=name).first()
        if person is not None:
            actors.append({"tvdb_id": person.tvdb_id, "name": person.name, "image": person.image})

    return render(request, "movies/list.html", {
        "current_year": current_year,
        "hero": hero,
        "genres": genres,
        "top_genres": top_genres,
        "top_countries": top_countries,
        "actors": actors,
    })


def header(request):
    """Header partial."""
    return render(request, "header.html")


def footer(request):
    """Footer partial."""
    return render(request, "footer.html", {
        "current_year": _jalali_year(),
    })