from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm, SignupForm

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
