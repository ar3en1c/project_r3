from django.db import models
from series.models import Genre, Person


class Movies(models.Model):
    tvdb_id = models.IntegerField(unique=True, db_index=True, verbose_name="آیدی تی وی دی بی", editable=False)
    schema_version = models.IntegerField(default=1, verbose_name="ورژن", editable=False)
    
    name = models.CharField(max_length=500, verbose_name="نام فیلم")
    slug = models.SlugField(max_length=500, unique=True, verbose_name="اسلاگ")
    image = models.URLField(max_length=1000, blank=True, verbose_name="تصویر")
    year = models.CharField(max_length=10, blank=True, verbose_name="سال ساخت")
    overview = models.TextField(blank=True, verbose_name="خلاصه داستان")
    
    # Metadata
    original_country = models.CharField(max_length=100, blank=True, verbose_name="کشور سازنده")
    original_language = models.CharField(max_length=50, blank=True, verbose_name="زبان اصلی")
    status = models.CharField(max_length=50, blank=True, verbose_name="وضعیت")
    rate = models.FloatField(blank=True, null=True, verbose_name="امتیاز")
    
    # English translations
    name_en = models.CharField(max_length=500, blank=True, verbose_name="نام انگلیسی")
    overview_en = models.TextField(blank=True, verbose_name="خلاصه داستان انگلیسی")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ به‌روزرسانی")

    # Persian Names
    
    name_fa = models.CharField(max_length=500, blank=True, null=True, verbose_name="نام فارسی")
    
    class Meta:
        db_table = 'movies'
        verbose_name = 'فیلم'
        verbose_name_plural = 'فیلم ها'
    
    def __str__(self):
        return f"{self.name} ({self.year})"


class MovieGenre(models.Model):
    movies = models.ForeignKey(Movies, on_delete=models.CASCADE, related_name='movie_genres', verbose_name="فیلم")
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, verbose_name="ژانر")
    
    class Meta:
        db_table = 'movies_genre_links'
        verbose_name = 'ژانر فیلم'
        verbose_name_plural = 'ژانر فیلم ها'
        unique_together = ('movies', 'genre')


class RemoteId(models.Model):
    movies = models.ForeignKey(Movies, on_delete=models.CASCADE, related_name='remote_ids', verbose_name="فیلم")
    remote_id = models.CharField(max_length=200, verbose_name="ریموت آیدی")
    id_type = models.IntegerField(verbose_name="نوع آیدی")
    source_name = models.CharField(max_length=100, verbose_name="نام منبع")
    
    class Meta:
        db_table = 'movies_remote_ids'
        unique_together = ('movies', 'source_name')
        indexes = [
            models.Index(fields=['remote_id', 'source_name']),
        ]
        verbose_name = 'ریموت ایدی'
        verbose_name_plural = 'ریموت آیدی ها'
    
    def __str__(self):
        return f"{self.source_name}: {self.remote_id}"


class Character(models.Model):
    tvdb_id = models.IntegerField(unique=True, db_index=True, verbose_name="آیدی تی وی دی بی")
    movies = models.ForeignKey(Movies, on_delete=models.CASCADE, related_name='characters', verbose_name="فیلم")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='movie_characters', verbose_name="شخص")
    
    character_name = models.CharField(max_length=300, verbose_name="نام کاراکتر")
    character_image = models.URLField(max_length=1000, blank=True, verbose_name="تصویر کاراکتر")
    people_type = models.CharField(max_length=50, default='Actor', verbose_name="نوع شخص")
    
    class Meta:
        db_table = 'movies_characters'
        verbose_name = 'کاراکتر'
        verbose_name_plural = 'کاراکتر ها'
        unique_together = ('movies', 'tvdb_id')
    
    def __str__(self):
        return f"{self.character_name} ({self.person.name})"


class TagOption(models.Model):
    movies = models.ForeignKey(Movies, on_delete=models.CASCADE, related_name='tag_options', verbose_name="فیلم")
    tvdb_id = models.IntegerField(verbose_name="آیدی تی وی دی بی")
    tag = models.IntegerField(verbose_name="تگ")
    tag_name = models.CharField(max_length=200, verbose_name="نام تگ")
    name = models.CharField(max_length=200, verbose_name="نام")
    
    class Meta:
        db_table = 'movies_tag_options'
        verbose_name = 'تگ اپشن'
        verbose_name_plural = 'تگ آپشن ها'
        unique_together = ('movies', 'tvdb_id')
