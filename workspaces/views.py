from django.shortcuts import render

from .models import Workspace


def workspace_list(request):
    workspaces = Workspace.objects.all()

    return render(
        request,
        "workspaces/workspace_list.html",
        {"workspaces": workspaces},
    )
