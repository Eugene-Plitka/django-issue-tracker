from django.urls import path

from . import views


app_name = "workspaces"

urlpatterns = [
    path("", views.workspace_list, name="list"),
    path("create/", views.workspace_create, name="create"),
    path("<slug:slug>/edit/", views.workspace_update, name="update"),
    path(
        "<slug:slug>/members/",
        views.workspace_member_list,
        name="member-list",
    ),
    path(
        "<slug:slug>/members/add/",
        views.workspace_member_add,
        name="member-add",
    ),
    path(
        "<slug:slug>/members/<int:membership_id>/edit/",
        views.workspace_member_update,
        name="member-update",
    ),
    path(
        "<slug:slug>/members/<int:membership_id>/delete/",
        views.workspace_member_delete,
        name="member-delete",
    ),
    path("<slug:slug>/", views.workspace_detail, name="detail"),
]
