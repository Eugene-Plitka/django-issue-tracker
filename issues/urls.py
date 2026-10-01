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
        "labels/create/",
        views.label_create,
        name="label-create",
    ),
    path(
        "labels/",
        views.label_list,
        name="label-list",
    ),
    path(
        "<int:issue_number>/delete/",
        views.issue_delete,
        name="delete",
    ),
    path(
        "<int:issue_number>/",
        views.issue_detail,
        name="detail",
    ),
    path("", views.issue_list, name="list"),
]
