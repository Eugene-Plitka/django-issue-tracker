from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "workspace", "created_at", "updated_at")
    search_fields = ("name", "key", "workspace__name")
    list_filter = ("workspace",)
