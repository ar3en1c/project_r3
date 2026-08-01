from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from series.models import Series
from .models import Track

# Create your views here.


def _ctx(obj, track):
    """Shared template context for the tracking partials."""
    return {
        "slug": obj.slug,
        "allEpisodes": obj.episode_count,
        "episodeWatched": track.progress or 0,
        "score": int(track.user_rate or 0),
        "track_status": track.status,
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


@login_required
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


@login_required
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


@login_required
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
