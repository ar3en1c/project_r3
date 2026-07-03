from django.shortcuts import render

# Create your views here.


def series(request):
    return render(request, "series/index.html")


def header(request):
    return render(request, "header.html")


def footer(request):
    return render(request, "footer.html")
