from django.db import models

# Create your models here.


class Movies(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام فیلم")
    slug = models.SlugField(verbose_name="اسلاگ فیلد")
    image = models.ImageField(upload_to="movies/poster/", verbose_name="پوستر")
    year = models.IntegerField(verbose_name="سال پخش")
    genres = models.ManyToManyField("Genres", verbose_name="ژانر")
    description = models.TextField(verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ")
    remoteIds = models.ManyToManyField("RemoteIds", verbose_name="شناسه های خارجی")
