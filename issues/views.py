from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from projects.models import Project
from workspaces.models import Workspace, WorkspaceMembership

from .forms import (
    CommentForm,
    IssueDeveloperForm,
    IssueForm,
    IssueManagementForm,
)
from .models import Activity, Issue
from .services import create_issue, update_issue_with_activity


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

    if request.method == "POST":
        if workspace_membership.role == WorkspaceMembership.Role.VIEWER:
            raise PermissionDenied

        comment_form = CommentForm(request.POST)

        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.issue = issue
            comment.author = request.user
            comment.save()

            return redirect(
                "issues:detail",
                workspace_slug=workspace.slug,
                project_key=project.key,
                issue_number=issue.number,
            )
    else:
        comment_form = CommentForm()

    return render(
        request,
        "issues/issue_detail.html",
        {
            "workspace": workspace,
            "project": project,
            "issue": issue,
            "workspace_membership": workspace_membership,
            "comment_form": comment_form,
        },
    )


@login_required
def issue_update(
    request,
    workspace_slug,
    project_key,
    issue_number,
):
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
        Issue,
        project=project,
        number=issue_number,
    )

    if workspace_membership.role == WorkspaceMembership.Role.VIEWER:
        raise PermissionDenied

    if workspace_membership.role in {
        WorkspaceMembership.Role.OWNER,
        WorkspaceMembership.Role.MANAGER,
    }:
        form_class = IssueManagementForm
        form_kwargs = {
            "project": project,
        }
    else:
        form_class = IssueDeveloperForm
        form_kwargs = {
            "project": project,
            "user": request.user,
        }

    if request.method == "POST":
        form = form_class(
            request.POST,
            instance=issue,
            **form_kwargs,
        )

        if form.is_valid():
            issue = update_issue_with_activity(
                issue=issue,
                actor=request.user,
                form=form,
            )

            if (
                workspace_membership.role == WorkspaceMembership.Role.DEVELOPER
                and form.cleaned_data.get("assign_to_me")
                and issue.assignee != request.user
            ):
                old_assignee = issue.assignee

                issue.assignee = request.user
                issue.save(update_fields=["assignee"])

                Activity.objects.create(
                    issue=issue,
                    actor=request.user,
                    action="changed",
                    field="assignee",
                    old_value=old_assignee.email if old_assignee else "",
                    new_value=request.user.email,
                )

            return redirect(
                "issues:detail",
                workspace_slug=workspace.slug,
                project_key=project.key,
                issue_number=issue.number,
            )
    else:
        form = form_class(
            instance=issue,
            **form_kwargs,
        )

    return render(
        request,
        "issues/issue_form.html",
        {
            "workspace": workspace,
            "project": project,
            "issue": issue,
            "form": form,
        },
    )
