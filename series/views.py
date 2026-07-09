from django.shortcuts import render
import jdatetime
# Create your views here.


def series(request):
    contex = {
        "score":9,
        "status": "dropped",
        "allEpisodes": 80,
        "episodeWatched": 70,
        "name": "بریکینگ بد",
        "year": "2008",
        "genres": ["درام","جنایی","هیجان انگیز","وسترن"],
    }
    return render(request, "series/index.html", contex)


def header(request):
    return render(request, "header.html")


def footer(request):
    return render(request, "footer.html")
