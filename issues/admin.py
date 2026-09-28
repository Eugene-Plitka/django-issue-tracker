from django.contrib import admin

from .models import Comment, Issue, Label


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


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("name", "project")
    search_fields = ("name", "project__name", "project__key")
    list_filter = ("project",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("issue", "author", "created_at", "updated_at")
    search_fields = ("body", "author__email", "issue__title")
    list_filter = ("created_at",)
