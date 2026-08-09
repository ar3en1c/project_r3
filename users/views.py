from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from movies.models import Movies
from series.models import Series
from tracking.models import Track
from tracking.views import htmx_login_required

from .forms import LoginForm, SignupForm
from .models import User

# Create your views here.


def _redirect_target(request):
    """Honor ?next= if present, otherwise go to the series list."""
    return request.GET.get("next") or request.POST.get("next") or "series:mainSeries"


def login_view(request):
    if request.user.is_authenticated:
        return redirect("series:mainSeries")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(_redirect_target(request))

    return render(request, "users/login.html", {
        "form": form,
        "next": request.GET.get("next", ""),
    })


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("series:mainSeries")

    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("series:mainSeries")

    return render(request, "users/signup.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("series:mainSeries")


# ---------------------------------------------------------------- profile

SERIES_STATUSES = [
    ("watching", "در حال تماشا"),
    ("plan to watch", "برنامه تماشا"),
    ("dropped", "رها شده"),
    ("completed", "تکمیل شده"),
]
MOVIE_STATUSES = [
    ("plan to watch", "برنامه تماشا"),
    ("completed", "تکمیل شده"),
    ("dropped", "رها شده"),
]


def _series_items(user):
    return list(Track.objects.filter(
        user=user, typeOfWatch="Series"
    ).select_related("serial").order_by("-updated_at"))


def _movie_items(user):
    return list(Track.objects.filter(
        user=user, typeOfWatch="Movie"
    ).select_related("movies").order_by("-updated_at"))


def _row(obj, t, total=None):
    """One profile-list row from a Track."""
    return {
        "slug": obj.slug,
        "name": obj.name_fa or obj.name,
        "image": obj.image,
        "ep": t.progress or 0,
        "total": total or 0,
        "rate": t.user_rate,
        "rated": bool(t.user_rate),
        "status": t.status,
        "status_display": t.get_status_display(),
    }


def _series_panel_ctx(user, read_only=False):
    items = _series_items(user)
    groups = []
    for value, label in SERIES_STATUSES:
        rows = [_row(t.serial, t, t.serial.episode_count)
                for t in items if t.status == value and t.serial]
        groups.append({"value": value, "label": label, "items": rows})
    return {
        "groups": groups,
        "status_options": SERIES_STATUSES,
        "stage_url": "users:series_stage",
        "panel_id": "series-panel",
        "kind": "series",
        "read_only": read_only,
    }


def _movie_panel_ctx(user, read_only=False):
    items = _movie_items(user)
    groups = []
    for value, label in MOVIE_STATUSES:
        rows = [_row(t.movies, t) for t in items if t.status == value and t.movies]
        groups.append({"value": value, "label": label, "items": rows})
    return {
        "groups": groups,
        "status_options": MOVIE_STATUSES,
        "stage_url": "users:movie_stage",
        "panel_id": "movie-panel",
        "kind": "movie",
        "read_only": read_only,
    }


def _profile_ctx(user, read_only=False):
    tracks = Track.objects.filter(user=user)
    rated = [t.user_rate for t in tracks.filter(user_rate__isnull=False)]
    avg = sum(rated) / len(rated) if rated else None
    stats = [
        {"value": tracks.filter(typeOfWatch="Series").count(), "label": "سریال"},
        {"value": tracks.filter(typeOfWatch="Movie").count(), "label": "فیلم"},
        {"value": tracks.filter(status="watching").count(), "label": "در حال تماشا"},
        {"value": tracks.filter(status="plan to watch").count(), "label": "برنامه تماشا"},
        {"value": tracks.filter(status="completed").count(), "label": "تکمیل شده"},
        {"value": avg and f"{avg:.1f}" or "—", "label": "میانگین امتیاز"},
    ]
    sctx = _series_panel_ctx(user, read_only=read_only)
    mctx = _movie_panel_ctx(user, read_only=read_only)
    return {
        "user": user,
        "stats": stats,
        "series_groups": sctx["groups"],
        "series_status_options": sctx["status_options"],
        "series_stage_url": sctx["stage_url"],
        "movie_groups": mctx["groups"],
        "movie_status_options": mctx["status_options"],
        "movie_stage_url": mctx["stage_url"],
        "read_only": read_only,
    }


@login_required
def profile_view(request):
    return redirect("users:public_profile", user_id=request.user.id)


def public_profile_view(request, user_id):
    """Anyone (logged in or not) can view a user's watch lists via a shareable link."""
    user = get_object_or_404(User, id=user_id)
    read_only = not request.user.is_authenticated or request.user.id != user.id
    return render(request, "users/index.html", _profile_ctx(user, read_only=read_only))


def _track_for(request, typeOfWatch, obj, **fk):
    track, _ = Track.objects.get_or_create(
        user=request.user, typeOfWatch=typeOfWatch, **fk,
        defaults={"status": "watching"},
    )
    return track


def _apply_rate(request, track, template, ctx):
    try:
        rate = int(request.POST.get("rate", ""))
    except ValueError:
        return HttpResponseBadRequest("invalid rate")
    if not 0 <= rate <= 10:
        return HttpResponseBadRequest("rate out of range")
    track.user_rate = rate or None  # 0 = clear the rating
    track.save()
    return render(request, template, ctx)


@htmx_login_required
@require_POST
def series_stage(request, slug):
    status = request.POST.get("status", "")
    if status not in {v for v, _ in SERIES_STATUSES}:
        return HttpResponseBadRequest("invalid status")
    obj = get_object_or_404(Series, slug=slug)
    track = _track_for(request, "Series", obj, serial=obj)
    track.status = status
    if status == "completed" and obj.episode_count:
        track.progress = obj.episode_count
    track.save()
    return render(request, "users/partials/panel.html", _series_panel_ctx(request.user))


@htmx_login_required
@require_POST
def series_step(request, slug):
    obj = get_object_or_404(Series, slug=slug)
    track = _track_for(request, "Series", obj, serial=obj)
    try:
        delta = int(request.POST.get("delta", "0"))
    except ValueError:
        return HttpResponseBadRequest("invalid delta")
    cap = obj.episode_count
    next_ep = (track.progress or 0) + delta
    if next_ep < 0 or (cap and next_ep > cap):
        return HttpResponseBadRequest("progress out of range")
    track.progress = next_ep
    if cap and next_ep >= cap:
        track.status = "completed"
    elif track.status == "completed":
        track.status = "watching"
    track.save()
    return render(request, "users/partials/panel.html", _series_panel_ctx(request.user))


@htmx_login_required
@require_POST
def rate(request):
    """Unified rating for the shared profile modal (type + slug in POST)."""
    kind = request.POST.get("type", "")
    slug = request.POST.get("slug", "")
    if kind == "series":
        obj = get_object_or_404(Series, slug=slug)
        track = _track_for(request, "Series", obj, serial=obj)
        return _apply_rate(request, track, "users/partials/panel.html", _series_panel_ctx(request.user))
    if kind == "movie":
        obj = get_object_or_404(Movies, slug=slug)
        track = _track_for(request, "Movie", obj, movies=obj)
        return _apply_rate(request, track, "users/partials/panel.html", _movie_panel_ctx(request.user))
    return HttpResponseBadRequest("invalid type")


@htmx_login_required
@require_POST
def movie_stage(request, slug):
    status = request.POST.get("status", "")
    if status not in {v for v, _ in MOVIE_STATUSES}:
        return HttpResponseBadRequest("invalid status")
    obj = get_object_or_404(Movies, slug=slug)
    track = _track_for(request, "Movie", obj, movies=obj)
    track.status = status
    track.save()
    return render(request, "users/partials/panel.html", _movie_panel_ctx(request.user))


