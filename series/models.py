from django.db import models

# Create your models here.
from django.db import models


class Series(models.Model):
    # Core fields
    tvdb_id = models.IntegerField(unique=True, db_index=True)
    schema_version = models.IntegerField(default=1)
    
    name = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True)
    image = models.URLField(max_length=1000, blank=True)
    year = models.CharField(max_length=10, blank=True)
    overview = models.TextField(blank=True)
    
    # Metadata
    original_country = models.CharField(max_length=100, blank=True)
    original_language = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=50, blank=True)
    episode_count = models.IntegerField(default=0)
    season_count = models.IntegerField(default=0)
    
    # English translations
    name_en = models.CharField(max_length=500, blank=True)
    overview_en = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'series'
        verbose_name = 'سریال'
        verbose_name_plural = 'سریال ها'
    
    def __str__(self):
        return f"{self.name} ({self.year})"


class Genre(models.Model):
    tvdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    
    class Meta:
        db_table = 'genres'
        verbose_name = 'ژانر'
        verbose_name_plural = 'ژانر ها'
    
    def __str__(self):
        return self.name


class SeriesGenre(models.Model):
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='series_genres')
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'series_genres'
        verbose_name = 'ژانر سریال'
        verbose_name_plural = 'ژانر سریال ها'
        unique_together = ('series', 'genre')


class RemoteId(models.Model):
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='remote_ids')
    remote_id = models.CharField(max_length=200)
    id_type = models.IntegerField()
    source_name = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'remote_ids'
        unique_together = ('series', 'source_name')
        indexes = [
            models.Index(fields=['remote_id', 'source_name']),
        ]
        verbose_name = 'ریموت ایدی'
        verbose_name_plural = 'ریموت آیدی ها'
    
    def __str__(self):
        return f"{self.source_name}: {self.remote_id}"


class Person(models.Model):
    tvdb_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=300)
    image = models.URLField(max_length=1000, blank=True, null=True)
    
    class Meta:
        db_table = 'people'
        verbose_name = 'شخص'
        verbose_name_plural = 'اشخاص'
    def __str__(self):
        return self.name


class Character(models.Model):
    tvdb_id = models.IntegerField(unique=True, db_index=True)
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='characters')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='characters')
    
    character_name = models.CharField(max_length=300)
    character_image = models.URLField(max_length=1000, blank=True)
    people_type = models.CharField(max_length=50, default='Actor')
    
    class Meta:
        db_table = 'characters'
        verbose_name = 'کاراکتر'
        verbose_name_plural = 'کاراکتر ها'
        unique_together = ('series', 'tvdb_id')
    
    def __str__(self):
        return f"{self.character_name} ({self.person.name})"


class TagOption(models.Model):
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='tag_options')
    tvdb_id = models.IntegerField()
    tag = models.IntegerField()
    tag_name = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    
    class Meta:
        db_table = 'tag_options'
        verbose_name = 'تگ اپشن'
        verbose_name_plural = 'تگ آپشن ها'
        unique_together = ('series', 'tvdb_id')
