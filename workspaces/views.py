from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User

from .forms import (
    WorkspaceForm,
    WorkspaceMemberForm,
    WorkspaceMemberRoleForm,
)
from .models import Workspace, WorkspaceMembership
from .permissions import (
    get_workspace_membership,
    require_workspace_management,
    require_workspace_owner,
)


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

    membership = get_workspace_membership(
        workspace,
        request.user,
    )

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

    require_workspace_owner(
        workspace,
        request.user,
    )

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


@login_required
def workspace_member_list(request, slug):
    workspace = get_object_or_404(
        Workspace,
        slug=slug,
        memberships__user=request.user,
    )

    current_membership = get_workspace_membership(
        workspace,
        request.user,
    )

    memberships = workspace.memberships.select_related("user").all()

    return render(
        request,
        "workspaces/workspace_member_list.html",
        {
            "workspace": workspace,
            "memberships": memberships,
            "current_membership": current_membership,
        },
    )


@login_required
def workspace_member_add(request, slug):
    workspace = get_object_or_404(
        Workspace,
        slug=slug,
        memberships__user=request.user,
    )

    current_membership = require_workspace_management(
        workspace,
        request.user,
    )

    if request.method == "POST":
        form = WorkspaceMemberForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            role = form.cleaned_data["role"]

            if (
                current_membership.role != WorkspaceMembership.Role.OWNER
                and role == WorkspaceMembership.Role.OWNER
            ):
                form.add_error(
                    "role",
                    "Only an owner can add another owner.",
                )
            else:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    form.add_error(
                        "email",
                        "No user with this email exists.",
                    )
                else:
                    if WorkspaceMembership.objects.filter(
                        workspace=workspace,
                        user=user,
                    ).exists():
                        form.add_error(
                            "email",
                            "This user is already a workspace member.",
                        )
                    else:
                        WorkspaceMembership.objects.create(
                            workspace=workspace,
                            user=user,
                            role=role,
                        )

                        return redirect(
                            "workspaces:member-list",
                            slug=workspace.slug,
                        )
    else:
        form = WorkspaceMemberForm()

    return render(
        request,
        "workspaces/workspace_member_form.html",
        {
            "workspace": workspace,
            "form": form,
        },
    )


@login_required
def workspace_member_update(request, slug, membership_id):
    workspace = get_object_or_404(
        Workspace,
        slug=slug,
        memberships__user=request.user,
    )

    current_membership = require_workspace_management(
        workspace,
        request.user,
    )

    membership = get_object_or_404(
        WorkspaceMembership,
        id=membership_id,
        workspace=workspace,
    )

    if request.method == "POST":
        form = WorkspaceMemberRoleForm(request.POST)

        if form.is_valid():
            new_role = form.cleaned_data["role"]

            if (
                current_membership.role != WorkspaceMembership.Role.OWNER
                and new_role == WorkspaceMembership.Role.OWNER
            ):
                form.add_error(
                    "role",
                    "Only an owner can assign the owner role.",
                )

            elif (
                membership.role == WorkspaceMembership.Role.OWNER
                and new_role != WorkspaceMembership.Role.OWNER
            ):
                owner_count = WorkspaceMembership.objects.filter(
                    workspace=workspace,
                    role=WorkspaceMembership.Role.OWNER,
                ).count()

                if owner_count == 1:
                    form.add_error(
                        "role",
                        "The last owner cannot be demoted.",
                    )
                else:
                    membership.role = new_role
                    membership.save(update_fields=["role"])

                    return redirect(
                        "workspaces:member-list",
                        slug=workspace.slug,
                    )

            else:
                membership.role = new_role
                membership.save(update_fields=["role"])

                return redirect(
                    "workspaces:member-list",
                    slug=workspace.slug,
                )

    else:
        form = WorkspaceMemberRoleForm(
            initial={"role": membership.role},
        )

    return render(
        request,
        "workspaces/workspace_member_update.html",
        {
            "workspace": workspace,
            "membership": membership,
            "form": form,
        },
    )


@login_required
def workspace_member_delete(request, slug, membership_id):
    workspace = get_object_or_404(
        Workspace,
        slug=slug,
        memberships__user=request.user,
    )

    current_membership = require_workspace_management(
        workspace,
        request.user,
    )

    membership = get_object_or_404(
        WorkspaceMembership,
        id=membership_id,
        workspace=workspace,
    )

    if (
        current_membership.role != WorkspaceMembership.Role.OWNER
        and membership.role == WorkspaceMembership.Role.OWNER
    ):
        raise PermissionDenied

    if membership.role == WorkspaceMembership.Role.OWNER:
        owner_count = WorkspaceMembership.objects.filter(
            workspace=workspace,
            role=WorkspaceMembership.Role.OWNER,
        ).count()

        if owner_count == 1:
            raise PermissionDenied

    if request.method == "POST":
        membership.delete()

        return redirect(
            "workspaces:member-list",
            slug=workspace.slug,
        )

    return render(
        request,
        "workspaces/workspace_member_confirm_delete.html",
        {
            "workspace": workspace,
            "membership": membership,
        },
    )
