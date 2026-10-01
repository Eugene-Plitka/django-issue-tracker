from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from projects.models import Project
from workspaces.models import Workspace, WorkspaceMembership

from .models import Issue


@login_required
def issue_list(request, workspace_slug, project_key):
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
        project = get_object_or_404(
            Project,
            workspace=workspace,
            key=project_key,
        )
    else:
        project = get_object_or_404(
            Project,
            workspace=workspace,
            key=project_key,
            memberships__user=request.user,
        )

    issues = Issue.objects.filter(
        project=project,
    ).select_related(
        "reporter",
        "assignee",
    )

    return render(
        request,
        "issues/issue_list.html",
        {
            "workspace": workspace,
            "project": project,
            "issues": issues,
            "workspace_membership": workspace_membership,
        },
    )
