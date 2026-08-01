from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from series.models import Series
from movies.models import Movies
from users.models import User
# Create your models here.


class Track(models.Model):
    types = [
        ("Series", "سریال"),
        ("Movie", "فیلم")
    ]
    progress_status = [
        ("completed", "تکمیل شده"),
        ("watching", "در حال تماشا"),
        ("dropped", "رها شده"),
        ("plan to watch", "برنامه_تماشا"),

    ]

    typeOfWatch = models.CharField(
        max_length=10, choices=types, verbose_name="نوع محتوا")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="کاربر")
    serial = models.ForeignKey(
        Series, on_delete=models.SET_NULL, verbose_name="سریال", null=True, blank=True)
    movies = models.ForeignKey(
        Movies, on_delete=models.SET_NULL, verbose_name="فیلم", null=True, blank=True)
    status = models.CharField(max_length=20, choices=progress_status, verbose_name="وضعیت تماشا")
    progress = models.IntegerField(verbose_name="چقدر تماشا شده", blank=True, null=True)
    user_rate = models.DecimalField(max_digits=3, decimal_places=1, verbose_name="نمره کاربر", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ به‌روزرسانی")

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "ردیابی"
        verbose_name_plural = "ردیابی ها"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'movies'],
                condition=Q(typeOfWatch='Movie'),
                name='uniq_user_movie',
            ),
            models.UniqueConstraint(
                fields=['user', 'serial'],
                condition=Q(typeOfWatch='Series'),
                name='uniq_user_series',
            ),
        ]

    def clean(self):
        # type must point at exactly one target FK
        if self.typeOfWatch == 'Movie' and not self.movies_id:
            raise ValidationError({'movies': "نوع محتوا فیلم است اما فیلمی انتخاب نشده."})
        if self.typeOfWatch == 'Series' and not self.serial_id:
            raise ValidationError({'serial': "نوع محتوا سریال است اما سریالی انتخاب نشده."})

        # bool/progress must agree
        if self.typeOfWatch == 'Movie' and self.progress:
            # ponytail: movies are atomic -- progress on a movie is meaningless, status alone suffices
            raise ValidationError({'progress': "برای فیلم نیازی به پیشرفت نیست — فقط وضعیت را ثبت کنید."})
        if self.status == 'completed' and self.typeOfWatch == 'Movie' and self.progress:
            self.progress = None

    def __str__(self):
        target = self.movies or self.serial
        return f"{self.user} → {target} ({self.get_typeOfWatch_display()})"
