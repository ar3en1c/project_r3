from django.shortcuts import render

# Create your views here.


def series(request):
    return render(request, "series/index.html", {"score": 10})


def header(request):
    return render(request, "header.html")


def footer(request):
    return render(request, "footer.html")
