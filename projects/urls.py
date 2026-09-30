from django.urls import path

from . import views


app_name = "projects"


urlpatterns = [
    path(
        "create/",
        views.project_create,
        name="create",
    ),
    path(
        "<str:project_key>/members/",
        views.project_member_list,
        name="member-list",
    ),
    path(
        "<str:project_key>/",
        views.project_detail,
        name="detail",
    ),
    path(
        "",
        views.project_list,
        name="list",
    ),
]
