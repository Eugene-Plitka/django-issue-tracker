from django.shortcuts import get_object_or_404

from workspaces.models import WorkspaceMembership

from .models import Project


def get_project_for_user(*, workspace, project_key, user):
    workspace_membership = workspace.memberships.get(
        user=user,
    )

    if workspace_membership.role in {
        WorkspaceMembership.Role.OWNER,
        WorkspaceMembership.Role.MANAGER,
    }:
        return get_object_or_404(
            Project,
            workspace=workspace,
            key=project_key,
        )

    return get_object_or_404(
        Project,
        workspace=workspace,
        key=project_key,
        memberships__user=user,
    )
