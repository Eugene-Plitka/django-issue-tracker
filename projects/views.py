from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from workspaces.models import Workspace, WorkspaceMembership
from workspaces.permissions import require_workspace_management

from .forms import ProjectForm, ProjectMemberForm
from .models import Project, ProjectMembership


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


@login_required
def project_create(request, workspace_slug):
    workspace = get_object_or_404(
        Workspace,
        slug=workspace_slug,
        memberships__user=request.user,
    )

    require_workspace_management(
        workspace,
        request.user,
    )

    if request.method == "POST":
        form = ProjectForm(request.POST)

        if form.is_valid():
            project = form.save(commit=False)
            project.workspace = workspace
            project.save()

            return redirect(
                "projects:list",
                workspace_slug=workspace.slug,
            )
    else:
        form = ProjectForm()

    return render(
        request,
        "projects/project_form.html",
        {
            "workspace": workspace,
            "form": form,
        },
    )


@login_required
def project_detail(request, workspace_slug, project_key):
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

    return render(
        request,
        "projects/project_detail.html",
        {
            "workspace": workspace,
            "project": project,
            "workspace_membership": workspace_membership,
        },
    )


@login_required
def project_member_list(request, workspace_slug, project_key):
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

    memberships = project.memberships.select_related("user").all()

    return render(
        request,
        "projects/project_member_list.html",
        {
            "workspace": workspace,
            "project": project,
            "memberships": memberships,
            "workspace_membership": workspace_membership,
        },
    )


@login_required
def project_member_add(request, workspace_slug, project_key):
    workspace = get_object_or_404(
        Workspace,
        slug=workspace_slug,
        memberships__user=request.user,
    )

    require_workspace_management(
        workspace,
        request.user,
    )

    project = get_object_or_404(
        Project,
        workspace=workspace,
        key=project_key,
    )

    if request.method == "POST":
        form = ProjectMemberForm(
            request.POST,
            workspace=workspace,
            project=project,
        )

        if form.is_valid():
            user = form.cleaned_data["user"]

            ProjectMembership.objects.create(
                project=project,
                user=user,
            )

            return redirect(
                "projects:member-list",
                workspace_slug=workspace.slug,
                project_key=project.key,
            )
    else:
        form = ProjectMemberForm(
            workspace=workspace,
            project=project,
        )

    return render(
        request,
        "projects/project_member_form.html",
        {
            "workspace": workspace,
            "project": project,
            "form": form,
        },
    )


@login_required
def project_member_delete(request, workspace_slug, project_key, membership_id):
    workspace = get_object_or_404(
        Workspace,
        slug=workspace_slug,
        memberships__user=request.user,
    )

    require_workspace_management(
        workspace,
        request.user,
    )

    project = get_object_or_404(
        Project,
        workspace=workspace,
        key=project_key,
    )

    membership = get_object_or_404(
        ProjectMembership,
        id=membership_id,
        project=project,
    )

    if request.method == "POST":
        membership.delete()

        return redirect(
            "projects:member-list",
            workspace_slug=workspace.slug,
            project_key=project.key,
        )

    return render(
        request,
        "projects/project_member_confirm_delete.html",
        {
            "workspace": workspace,
            "project": project,
            "membership": membership,
        },
    )
