from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import WorkspaceForm
from .models import Workspace, WorkspaceMembership


@login_required
def workspace_list(request):
    workspaces = Workspace.objects.filter(memberships__user=request.user)

    return render(
        request,
        "workspaces/workspace_list.html",
        {"workspaces": workspaces},
    )


@login_required
def workspace_detail(request, slug):
    workspace = get_object_or_404(
        Workspace,
        slug=slug,
        memberships__user=request.user,
    )

    membership = workspace.memberships.get(user=request.user)

    return render(
        request,
        "workspaces/workspace_detail.html",
        {
            "workspace": workspace,
            "membership": membership,
        },
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


@login_required
def workspace_update(request, slug):
    workspace = get_object_or_404(
        Workspace,
        slug=slug,
        memberships__user=request.user,
    )

    membership = workspace.memberships.get(user=request.user)

    if membership.role != WorkspaceMembership.Role.OWNER:
        raise PermissionDenied

    if request.method == "POST":
        form = WorkspaceForm(request.POST, instance=workspace)

        if form.is_valid():
            workspace = form.save()

            return redirect(
                "workspaces:detail",
                slug=workspace.slug,
            )
    else:
        form = WorkspaceForm(instance=workspace)

    return render(
        request,
        "workspaces/workspace_form.html",
        {
            "form": form,
            "workspace": workspace,
        },
    )
