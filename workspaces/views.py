from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import WorkspaceForm
from .models import Workspace, WorkspaceMembership


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


@login_required
def workspace_create(request):
    if request.method == "POST":
        form = WorkspaceForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                workspace = form.save()

                WorkspaceMembership.objects.create(
                    workspace=workspace,
                    user=request.user,
                    role=WorkspaceMembership.Role.OWNER,
                )

            return redirect(
                "workspaces:detail",
                slug=workspace.slug,
            )
    else:
        form = WorkspaceForm()

    return render(
        request,
        "workspaces/workspace_form.html",
        {"form": form},
    )
