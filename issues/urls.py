from django.urls import path

from . import views


app_name = "issues"

urlpatterns = [
    path(
        "create/",
        views.issue_create,
        name="create",
    ),
    path("", views.issue_list, name="list"),
]
