from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from tracking.models import Track


@login_required
def home(request):
    # Continue-watching: series the user is watching, most recently updated first.
    continued = (
        Track.objects
        .filter(user=request.user, typeOfWatch="Series", status="watching", serial__isnull=False)
        .select_related("serial")
        .order_by("-updated_at")[:10]
    )
    return render(request, "home/index.html", {"continued": continued})