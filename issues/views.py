from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from projects.models import Project
from workspaces.models import Workspace, WorkspaceMembership

from .forms import IssueForm
from .models import Issue
from .services import create_issue


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


@login_required
def issue_create(request, workspace_slug, project_key):
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

    if workspace_membership.role == WorkspaceMembership.Role.VIEWER:
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied

    if request.method == "POST":
        form = IssueForm(
            request.POST,
            project=project,
        )

        if form.is_valid():
            issue = create_issue(
                project=project,
                reporter=request.user,
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                priority=form.cleaned_data["priority"],
                assignee=form.cleaned_data["assignee"],
            )

            return redirect(
                "issues:list",
                workspace_slug=workspace.slug,
                project_key=project.key,
            )
    else:
        form = IssueForm(project=project)

    return render(
        request,
        "issues/issue_form.html",
        {
            "workspace": workspace,
            "project": project,
            "form": form,
        },
    )


@login_required
def issue_detail(request, workspace_slug, project_key, issue_number):
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

    issue = get_object_or_404(
        Issue.objects.select_related(
            "reporter",
            "assignee",
        ).prefetch_related(
            "labels",
            "comments__author",
            "activities__actor",
        ),
        project=project,
        number=issue_number,
    )

    return render(
        request,
        "issues/issue_detail.html",
        {
            "workspace": workspace,
            "project": project,
            "issue": issue,
            "workspace_membership": workspace_membership,
        },
    )
