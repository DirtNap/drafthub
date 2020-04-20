from django.contrib import admin
from .models import Draft, Tag


@admin.register(Draft)
class DraftAdmin(admin.ModelAdmin):
    fields = ('blog', 'github_url', 'title', 'view_count', 'abstract', 'tags', 'slug', 'pub_date', 'last_update')
    readonly_fields = ('view_count', 'slug', 'pub_date', 'last_update')

    list_display = ('blog', 'title', 'view_count', 'slug', 'pub_date', 'last_update')
    list_filter = ('blog', 'pub_date', 'last_update', 'tags')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass
