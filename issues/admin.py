from django.contrib import admin

from .models import Issue


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "number",
        "status",
        "priority",
        "reporter",
        "assignee",
        "created_at",
    )
    list_filter = ("status", "priority", "project")
    search_fields = (
        "title",
        "description",
        "project__name",
        "project__key",
        "reporter__email",
        "assignee__email",
    )
