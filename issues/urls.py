from django.urls import path

from . import views

app_name = "issues"

urlpatterns = [
    path(
        "create/",
        views.issue_create,
        name="create",
    ),
    path(
        "<int:issue_number>/edit/",
        views.issue_update,
        name="update",
    ),
    path(
        "<int:issue_number>/",
        views.issue_detail,
        name="detail",
    ),
    path("", views.issue_list, name="list"),
]
