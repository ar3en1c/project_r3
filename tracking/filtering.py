"""Shared queryset filtering for the series/movies list pages.

Kept in tracking/ (already a shared app) — nothing here touches Track.
"""
from django.db.models import Q

PER_PAGE = 24


def filter_qs(qs, request, countries, sort_opts):
    """Apply genre/country/year/rate filters + sort/offset from GET params.
    Returns (page_qs, context_dict_for_the_panel)."""
    genre = request.GET.get("genre", "")
    country = request.GET.get("country", "")
    year = request.GET.get("year", "")
    rate = request.GET.get("rate", "")
    sort = request.GET.get("sort", "")
    try:
        offset = max(int(request.GET.get("offset", "0")), 0)
    except ValueError:
        offset = 0

    if genre:
        qs = qs.filter(**{f"{qs.model._meta.model_name}_genres__genre__slug": genre})
    if country:
        qs = qs.filter(original_country=country)
    if year:
        qs = qs.filter(year=year)
    if rate:
        qs = qs.filter(rate__gte=float(rate))

    qs = qs.exclude(image="").exclude(rate__isnull=True)

    sort_map = dict(sort_opts)
    qs = qs.order_by(sort_map.get(sort, sort_opts[0][0]))

    total = qs.count()
    page = list(qs[offset : offset + PER_PAGE])
    return page, {
        "genre": genre,
        "country": country,
        "year": year,
        "rate": rate,
        "sort": sort,
        "offset_next": offset + PER_PAGE,
        "has_more": offset + PER_PAGE < total,
    }
