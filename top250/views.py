from django.shortcuts import render

# Create your views here.


def top250_view(request):
    return render(request, "top250/index.html")
