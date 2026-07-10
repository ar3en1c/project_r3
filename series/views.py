from django.shortcuts import render
# Create your views here.


def series(request):
    contex = {
        # Hero
        "name": "بریکینگ بد",
        "year": "2008",
        "page_title_suffix": "جزئیات سریال",
        "genres": ["درام", "جنایی", "هیجان انگیز", "وسترن"],
        "poster_url": "https://artworks.thetvdb.com/banners/posters/81189-10.jpg",
        "poster_alt": "بریکینگ بد",

        # Status / progress
        "status": "dropped",
        "allEpisodes": 80,
        "episodeWatched": 70,
        "score": 9,

        # Status card (right column)
        "status_label": "پایان یافته",
        "total_seasons": 5,
        "total_units": 80,           # "واحدها" mirrors total episodes conceptually

        # Metadata card
        "imdb_id": "tt0903747",
        "language": "انگلیسی (EN-US)",
        "country": "آمریکا",

        # Overview
        "overview": "وقتی والتر وایت، یک معلم شیمی، مبتلا به سرطان مرحله III تشخیص داده می‌شود و پیش‌آگاهی دو سال زندگی برایش داده می‌شود، او انتخاب می‌کند که وارد دنیای خطرناک مواد مخدر و جنایت شود با هدف تأمین امنیت مالی خانواده‌اش.",

        # Characters: list of dicts so the template can loop
        "characters": [
            {"name": "اسکایلر وایت",        "actor": "آنا گان",          "image": "https://artworks.thetvdb.com/banners/actors/75476.jpg"},
            {"name": "جسی پینکمن",          "actor": "آرون پل",          "image": "https://artworks.thetvdb.com/banners/actors/75477.jpg"},
            {"name": "هنک شریدر",            "actor": "دین نوریس",        "image": "https://artworks.thetvdb.com/banners/actors/75478.jpg"},
            {"name": "ماری شریدر",            "actor": "بتسی برانت",       "image": "https://artworks.thetvdb.com/banners/actors/75479.jpg"},
            {"name": "والتر وایت جونیور",    "actor": "آر جی میته",      "image": "https://artworks.thetvdb.com/banners/actors/75480.jpg"},
            {"name": "والتر وایت",           "actor": "برایان کرانستون",  "image": "https://artworks.thetvdb.com/banners/actors/80112.jpg"},
            {"name": "سائول گودمن",          "actor": "باب اودنکرک",     "image": "https://artworks.thetvdb.com/banners/actors/289551.jpg"},
            {"name": "گوستاوو فرینگ",        "actor": "جیانکارلو اسپوزیتو", "image": "https://artworks.thetvdb.com/banners/actors/289552.jpg"},
            {"name": "مایک ارمانتراوت",      "actor": "جاناتان بنکس",    "image": "https://artworks.thetvdb.com/banners/actors/289553.jpg"},
        ],

        # Status buttons: (value, label) tuples so the list/order/labels stay in Python
        "status_options": [
            ("completed", "تکمیل شده"),
            ("watching", "در حال تماشا"),
            ("dropped", "رها شده"),
            ("plan to watch", "برنامه_تماشا"),
        ],
    }
    return render(request, "series/index.html", contex)


def header(request):
    return render(request, "header.html")


def footer(request):
    return render(request, "footer.html")
