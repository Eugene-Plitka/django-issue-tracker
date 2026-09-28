from django.shortcuts import get_object_or_404, render

from .models import Workspace


def workspace_list(request):
    workspaces = Workspace.objects.all()

    return render(
        request,
        "workspaces/workspace_list.html",
        {"workspaces": workspaces},
    )


def workspace_detail(request, slug):
    workspace = get_object_or_404(
        Workspace,
        slug=slug,
    )

    return render(
        request,
        "workspaces/workspace_detail.html",
        {"workspace": workspace},
    )
