from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from workspaces.models import Workspace, WorkspaceMembership

from .models import Project


@login_required
def project_list(request, workspace_slug):
    workspace = get_object_or_404(
        Workspace,
        slug=workspace_slug,
        memberships__user=request.user,
    )

    workspace_membership = workspace.memberships.get(
        user=request.user,
    )

    if workspace_membership.role in {
        WorkspaceMembership.Role.OWNER,
        WorkspaceMembership.Role.MANAGER,
    }:
        projects = workspace.projects.all()
    else:
        projects = workspace.projects.filter(
            memberships__user=request.user,
        )

    return render(
        request,
        "projects/project_list.html",
        {
            "workspace": workspace,
            "projects": projects,
            "workspace_membership": workspace_membership,
        },
    )
