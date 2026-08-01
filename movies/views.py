"""Movie views."""
from django.shortcuts import render, get_object_or_404
import jdatetime

from .models import Movies


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

    context = {
        # Hero
        "name": obj.name_fa or obj.name,
        "year": obj.year,
        "page_title_suffix": "جزئیات فیلم",
        "genres": genres,
        "poster_url": obj.image,
        "poster_alt": obj.name_fa or obj.name,

        # Status / progress
        "status": obj.status or "",
        "allEpisodes": 1,  # Movies have only 1 "episode"
        "episodeWatched": 0,
        "score": 0,  # User rating (to be implemented)

        # IMDb rating (from TVDB/IMDb import)
        "imdb_rate": obj.rate,

        # Status card (right column)
        "status_label": "تمام شده" if obj.status == "Released" else "در حال پخش" if obj.status else "نامشخص",
        "total_seasons": 0,  # Movies don't have seasons
        "total_units": 1,  # Movies have 1 unit

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


def header(request):
    """Header partial."""
    return render(request, "header.html")


def footer(request):
    """Footer partial."""
    return render(request, "footer.html", {
        "current_year": _jalali_year(),
    })