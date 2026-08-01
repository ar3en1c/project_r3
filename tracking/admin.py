from django.contrib import admin

from .models import Track


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('user', 'typeOfWatch', 'serial', 'movies', 'status', 'progress', 'user_rate', 'updated_at')
    list_filter = ('typeOfWatch', 'status', 'updated_at')
    search_fields = ('user__username', 'serial__name', 'movies__name')
    autocomplete_fields = ('user', 'serial', 'movies')
    list_select_related = ('user', 'serial', 'movies')
    list_per_page = 50
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')
