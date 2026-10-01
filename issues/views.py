import re

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Case, IntegerField, Value, When, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from projects.models import Project
from workspaces.models import Workspace, WorkspaceMembership
from workspaces.permissions import require_workspace_management

from .forms import (
    CommentForm,
    IssueDeveloperForm,
    IssueForm,
    IssueManagementForm,
    LabelForm,
)
from .models import Activity, Issue
from .services import (
    create_comment_activity,
    create_issue,
    update_issue_with_activity,
)


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

    issues = (
        Issue.objects.filter(project=project)
        .select_related(
            "reporter",
            "assignee",
        )
        .prefetch_related("labels")
    )

    status = request.GET.get("status")
    priority = request.GET.get("priority")
    assignee = request.GET.get("assignee")
    label = request.GET.get("label")
    query = request.GET.get("q")
    sort = request.GET.get("sort", "created")

    if status:
        issues = issues.filter(status=status)

    if priority:
        issues = issues.filter(priority=priority)

    if assignee:
        issues = issues.filter(assignee_id=assignee)

    if label:
        issues = issues.filter(labels__id=label)

    if query:
        issue_key_match = re.fullmatch(
            r"([A-Za-z0-9_-]+)-(\d+)",
            query.strip(),
        )

        if issue_key_match:
            project_key, issue_number = issue_key_match.groups()

            issues = issues.filter(
                project__key__iexact=project_key,
                number=issue_number,
            )
        else:
            issues = issues.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(project__key__icontains=query)
            )

    issues = issues.distinct()

    issues = issues.annotate(
        priority_order=Case(
            When(priority=Issue.Priority.CRITICAL, then=Value(1)),
            When(priority=Issue.Priority.HIGH, then=Value(2)),
            When(priority=Issue.Priority.MEDIUM, then=Value(3)),
            When(priority=Issue.Priority.LOW, then=Value(4)),
            output_field=IntegerField(),
        )
    )

    assignees = User.objects.filter(
        project_memberships__project=project,
    ).distinct()

    sort_options = {
        "created": "-created_at",
        "updated": "-updated_at",
        "priority": "priority_order",
        "status": "status",
    }

    issues = issues.order_by(sort_options.get(sort, "-created_at"))

    labels = project.labels.all()

    return render(
        request,
        "issues/issue_list.html",
        {
            "workspace": workspace,
            "project": project,
            "issues": issues,
            "workspace_membership": workspace_membership,
            "assignees": assignees,
            "labels": labels,
            "selected_status": status,
            "selected_priority": priority,
            "selected_assignee": assignee,
            "selected_label": label,
            "status_choices": Issue.Status.choices,
            "priority_choices": Issue.Priority.choices,
            "search_query": query,
            "selected_sort": sort,
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

            create_comment_activity(
                issue=issue,
                actor=request.user,
            )

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


@login_required
def label_list(request, workspace_slug, project_key):
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

    labels = project.labels.all()

    return render(
        request,
        "issues/label_list.html",
        {
            "workspace": workspace,
            "project": project,
            "labels": labels,
            "workspace_membership": workspace_membership,
        },
    )


@login_required
def label_create(request, workspace_slug, project_key):
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
        form = LabelForm(request.POST)

        if form.is_valid():
            label = form.save(commit=False)
            label.project = project
            label.save()

            return redirect(
                "issues:label-list",
                workspace_slug=workspace.slug,
                project_key=project.key,
            )
    else:
        form = LabelForm()

    return render(
        request,
        "issues/label_form.html",
        {
            "workspace": workspace,
            "project": project,
            "form": form,
        },
    )
