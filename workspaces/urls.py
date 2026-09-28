from django.urls import path

from . import views


app_name = "workspaces"

urlpatterns = [
    path("", views.workspace_list, name="list"),
    path("<slug:slug>/", views.workspace_detail, name="detail"),
]
