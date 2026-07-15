from django.contrib import admin
from .models import Series, Genre, SeriesGenre, RemoteId, Person, Character, TagOption


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('tvdb_id', 'name', 'year', 'status', 'episode_count', 'season_count', 'rate', 'created_at')
    list_filter = ('status', 'original_country', 'original_language', 'created_at')
    search_fields = ('name', 'slug', 'name_en', 'overview', 'tvdb_id')
    readonly_fields = ('tvdb_id', 'schema_version', 'created_at', 'updated_at')
    list_per_page = 50
    ordering = ('-created_at',)

    fieldsets = (
        ('Core', {
            'fields': ('name', 'slug', 'image', 'year', 'overview')
        }),
        ('Metadata', {
            'fields': ('original_country', 'original_language', 'status', 'episode_count', 'season_count', 'rate')
        }),
        ('Translations', {
            'fields': ('name_en', 'overview_en', 'name_fa')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('tvdb_id', 'name', 'slug')
    search_fields = ('name', 'slug', 'tvdb_id')
    list_per_page = 50


@admin.register(SeriesGenre)
class SeriesGenreAdmin(admin.ModelAdmin):
    list_display = ('series', 'genre')
    list_filter = ('genre',)
    search_fields = ('series__name', 'genre__name')
    list_per_page = 50
    autocomplete_fields = ('series', 'genre')


@admin.register(RemoteId)
class RemoteIdAdmin(admin.ModelAdmin):
    list_display = ('series', 'source_name', 'remote_id', 'id_type')
    list_filter = ('source_name', 'id_type')
    search_fields = ('series__name', 'remote_id', 'source_name')
    list_per_page = 50
    autocomplete_fields = ('series',)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('tvdb_id', 'name', 'image')
    search_fields = ('name', 'tvdb_id')
    list_per_page = 50


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('tvdb_id', 'series', 'person', 'character_name', 'people_type')
    list_filter = ('people_type', 'series')
    search_fields = ('character_name', 'series__name', 'person__name')
    list_per_page = 50
    autocomplete_fields = ('series', 'person')


@admin.register(TagOption)
class TagOptionAdmin(admin.ModelAdmin):
    list_display = ('series', 'tvdb_id', 'tag', 'tag_name', 'name')
    list_filter = ('tag',)
    search_fields = ('series__name', 'tag_name', 'name')
    list_per_page = 50
    autocomplete_fields = ('series',)