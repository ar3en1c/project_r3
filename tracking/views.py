from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from series.models import Series
from movies.models import Movies
from .models import Track

# Create your views here.


def htmx_login_required(view):
    """Like login_required, but answers HTMX requests with HX-Redirect
    so the browser does a full-page redirect instead of swapping the
    login page HTML into the target element."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = f"{reverse('users:login')}?next={request.path}"
            if request.headers.get("HX-Request"):
                response = HttpResponse(status=204)
                response["HX-Redirect"] = login_url
                return response
            return redirect(login_url)
        return view(request, *args, **kwargs)

    return wrapper


def _ctx(obj, track):
    """Shared template context for the tracking partials."""
    return {
        "slug": obj.slug,
        "allEpisodes": obj.episode_count,
        "episodeWatched": track.progress or 0,
        "score": int(track.user_rate or 0),
        "track_status": track.status,
        "favorite": track.favorite,
        "status_options": Track.progress_status,
    }


def _movie_ctx(obj, track):
    """Shared template context for the movie tracking partials."""
    return {
        "slug": obj.slug,
        "score": int(track.user_rate or 0),
        "track_status": track.status,
        "favorite": track.favorite,
        "status_options": Track.progress_status,
    }


def _get_series_track(user, slug):
    obj = get_object_or_404(Series, slug=slug)
    track, _ = Track.objects.get_or_create(
        user=user,
        typeOfWatch="Series",
        serial=obj,
        defaults={"status": "watching"},
    )
    return obj, track


@htmx_login_required
@require_POST
def set_series_status(request, slug):
    status = request.POST.get("status", "")
    valid = {value for value, _ in Track.progress_status}
    if status not in valid:
        return HttpResponseBadRequest("invalid status")

    obj, track = _get_series_track(request.user, slug)
    track.status = status
    if status == "completed" and obj.episode_count:
        track.progress = obj.episode_count
    track.save()

    ctx = _ctx(obj, track)
    html = render_to_string("series/partials/status_buttons.html", ctx, request)
    # progress may have changed too (completed) -> refresh it out-of-band
    html += render_to_string("series/partials/progress.html", {**ctx, "oob": True}, request)
    return HttpResponse(html)


@htmx_login_required
@require_POST
def set_series_progress(request, slug):
    obj, track = _get_series_track(request.user, slug)
    try:
        progress = int(request.POST.get("progress", ""))
    except ValueError:
        return HttpResponseBadRequest("invalid progress")
    if progress < 0 or (obj.episode_count and progress > obj.episode_count):
        return HttpResponseBadRequest("progress out of range")

    track.progress = progress
    track.save()
    return render(request, "series/partials/progress.html", _ctx(obj, track))


@htmx_login_required
@require_POST
def set_series_rating(request, slug):
    obj, track = _get_series_track(request.user, slug)
    try:
        rate = int(request.POST.get("rate", ""))
    except ValueError:
        return HttpResponseBadRequest("invalid rate")
    if not 1 <= rate <= 10:
        return HttpResponseBadRequest("rate out of range")

    track.user_rate = rate
    track.save()
    return render(request, "series/partials/rating.html", _ctx(obj, track))


def _get_movie_track(user, slug):
    obj = get_object_or_404(Movies, slug=slug)
    track, _ = Track.objects.get_or_create(
        user=user,
        typeOfWatch="Movie",
        movies=obj,
        defaults={"status": "watching"},
    )
    return obj, track


@htmx_login_required
@require_POST
def set_movie_status(request, slug):
    status = request.POST.get("status", "")
    valid = {value for value, _ in Track.progress_status}
    if status not in valid:
        return HttpResponseBadRequest("invalid status")

    obj, track = _get_movie_track(request.user, slug)
    track.status = status
    track.save()

    return render(request, "movies/partials/status_buttons.html", _movie_ctx(obj, track))


@htmx_login_required
@require_POST
def set_movie_rating(request, slug):
    obj, track = _get_movie_track(request.user, slug)
    try:
        rate = int(request.POST.get("rate", ""))
    except ValueError:
        return HttpResponseBadRequest("invalid rate")
    if not 1 <= rate <= 10:
        return HttpResponseBadRequest("rate out of range")

    track.user_rate = rate
    track.save()
    return render(request, "movies/partials/rating.html", _movie_ctx(obj, track))


@htmx_login_required
@require_POST
def toggle_series_favorite(request, slug):
    obj, track = _get_series_track(request.user, slug)
    track.favorite = not track.favorite
    track.save(update_fields=["favorite", "updated_at"])
    return render(request, "series/partials/favorite.html", _ctx(obj, track))


@htmx_login_required
@require_POST
def toggle_movie_favorite(request, slug):
    obj, track = _get_movie_track(request.user, slug)
    track.favorite = not track.favorite
    track.save(update_fields=["favorite", "updated_at"])
    return render(request, "movies/partials/favorite.html", _movie_ctx(obj, track))


# ---------------------------------------------------------------- favorites page

def _fav_row(obj, track, kind):
    return {
        "kind": kind,
        "slug": obj.slug,
        "name": obj.name_fa or obj.name,
        "image": obj.image,
        "year": obj.year,
        "rate": obj.rate,
    }


@login_required
def favorites_view(request):
    favs = Track.objects.filter(user=request.user, favorite=True).select_related("serial", "movies").order_by("-updated_at")
    movies = [_fav_row(t.movies, t, "movie") for t in favs if t.typeOfWatch == "Movie" and t.movies]
    series = [_fav_row(t.serial, t, "series") for t in favs if t.typeOfWatch == "Series" and t.serial]
    return render(request, "tracking/favorites.html", {"movies": movies, "series": series})


@htmx_login_required
@require_POST
def remove_favorite(request):
    """Remove a favorite by type+slug. Returns the refreshed whole panel (both tabs)
    so the removed item disappears without a full page reload."""
    kind = request.POST.get("type", "")
    slug = request.POST.get("slug", "")
    if kind == "series":
        track = Track.objects.filter(
            user=request.user, typeOfWatch="Series", serial__slug=slug).first()
    elif kind == "movie":
        track = Track.objects.filter(
            user=request.user, typeOfWatch="Movie", movies__slug=slug).first()
    else:
        return HttpResponseBadRequest("invalid type")

    if track:
        track.favorite = False
        track.save(update_fields=["favorite", "updated_at"])

    # rebuild both panels for the response
    movies = [_fav_row(t.movies, t, "movie")
              for t in Track.objects.filter(user=request.user, favorite=True, typeOfWatch="Movie").select_related("movies")
              if t.movies]
    series = [_fav_row(t.serial, t, "series")
              for t in Track.objects.filter(user=request.user, favorite=True, typeOfWatch="Series").select_related("serial")
              if t.serial]
    return render(request, "tracking/partials/fav_list.html", {"movies": movies, "series": series})
