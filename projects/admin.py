from django.contrib import admin

from .models import Project, ProjectMembership


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "workspace", "created_at", "updated_at")
    search_fields = ("name", "key", "workspace__name")
    list_filter = ("workspace",)


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "joined_at")
    search_fields = ("user__email", "project__name", "project__key")
    list_filter = ("project",)
