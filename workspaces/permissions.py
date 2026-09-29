from django.core.exceptions import PermissionDenied

from .models import WorkspaceMembership


def get_workspace_membership(workspace, user):
    return workspace.memberships.get(user=user)


def require_workspace_owner(workspace, user):
    membership = get_workspace_membership(workspace, user)

    if membership.role != WorkspaceMembership.Role.OWNER:
        raise PermissionDenied

    return membership


def require_workspace_management(workspace, user):
    membership = get_workspace_membership(workspace, user)

    allowed_roles = {
        WorkspaceMembership.Role.OWNER,
        WorkspaceMembership.Role.MANAGER,
    }

    if membership.role not in allowed_roles:
        raise PermissionDenied

    return membership
