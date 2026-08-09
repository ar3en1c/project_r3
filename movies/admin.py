from django.contrib import admin
from django.utils.html import format_html

from .models import Movies, MovieGenre, RemoteId, Character, TagOption


class MovieGenreInline(admin.TabularInline):
    model = MovieGenre
    extra = 1
    autocomplete_fields = ('genre',)
    verbose_name = 'ژانر'
    verbose_name_plural = 'ژانرها'


class RemoteIdInline(admin.TabularInline):
    model = RemoteId
    extra = 0
    verbose_name = 'ریموت آیدی'
    verbose_name_plural = 'ریموت آیدی‌ها'


class CharacterInline(admin.TabularInline):
    model = Character
    extra = 0
    autocomplete_fields = ('person',)
    verbose_name = 'کاراکتر'
    verbose_name_plural = 'کاراکترها'
    fields = ('person', 'character_name', 'people_type', 'tvdb_id', 'character_image')


class TagOptionInline(admin.TabularInline):
    model = TagOption
    extra = 0
    verbose_name = 'تگ آپشن'
    verbose_name_plural = 'تگ آپشن‌ها'


@admin.register(Movies)
class MoviesAdmin(admin.ModelAdmin):
    list_display = ('poster', 'name', 'name_fa', 'year', 'rate', 'status', 'updated_at',)
    list_display_links = ('poster', 'name')
    list_filter = ('status', 'original_language', 'original_country', 'year')
    search_fields = ('name', 'name_en', 'name_fa', 'slug', 'tvdb_id')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('tvdb_id', 'schema_version', 'created_at', 'updated_at', 'poster_preview')
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ('-updated_at',)
    inlines = (MovieGenreInline, RemoteIdInline, CharacterInline, TagOptionInline)

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                ('name', 'name_en', 'name_fa'),
                'slug',
                ('year', 'status', 'rate'),
                'poster_preview', 'image',
            ),
        }),
        ('توضیحات', {
            'fields': ('overview', 'overview_en'),
            'classes': ('collapse',),
        }),
        ('متادیتا', {
            'fields': (
                ('original_country', 'original_language'),
                ('tvdb_id', 'schema_version'),
            ),
        }),
        ('پخش آنلاین', {
            'fields': (('filimo', 'namava'),),
        }),
        ('زمان‌بندی', {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='تصویر')
    def poster(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:40px;height:60px;object-fit:cover;border-radius:4px;" />',
                obj.image,
            )
        return '—'

    @admin.display(description='پیش‌نمایش تصویر')
    def poster_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:200px;border-radius:6px;" />',
                obj.image,
            )
        return '—'


@admin.register(RemoteId)
class RemoteIdAdmin(admin.ModelAdmin):
    list_display = ('movies', 'source_name', 'remote_id', 'id_type')
    list_filter = ('source_name',)
    search_fields = ('remote_id', 'movies__name', 'movies__name_fa')
    autocomplete_fields = ('movies',)
    list_per_page = 50


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('character_name', 'person', 'movies', 'people_type')
    list_filter = ('people_type',)
    search_fields = ('character_name', 'person__name', 'movies__name', 'movies__name_fa')
    autocomplete_fields = ('movies', 'person')
    list_per_page = 50


@admin.register(TagOption)
class TagOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'tag_name', 'tag', 'movies', 'tvdb_id')
    list_filter = ('tag_name',)
    search_fields = ('name', 'tag_name', 'movies__name', 'movies__name_fa')
    autocomplete_fields = ('movies',)
    list_per_page = 50
