from django.shortcuts import render, get_object_or_404
import jdatetime

from .models import Series

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
        }
        for c in obj.characters.select_related("person").all()
    ]

    imdb_id = next(
        (r.remote_id for r in obj.remote_ids.all() if r.source_name.lower() == "imdb"),
        "",
    )

    contex = {
        # Hero
        "name": obj.name_fa or obj.name,
        "year": obj.year,
        "page_title_suffix": "جزئیات سریال",
        "genres": [g.genre.name for g in obj.series_genres.select_related("genre").all()],
        "poster_url": obj.image,
        "poster_alt": obj.name_fa or obj.name,

        # Status / progress
        "status": obj.status or "",
        "allEpisodes": obj.episode_count,
        "episodeWatched": 0,
        "score": obj.rate or 0,

        # Status card (right column)
        "status_label": obj.status or "نامشخص",
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


def header(request):
    return render(request, "header.html")


def footer(request):
    return render(request, "footer.html", {
        "current_year": _jalali_year(),
    })

