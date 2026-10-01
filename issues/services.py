from django.db import transaction

from projects.models import Project

from .models import Activity, Issue


@transaction.atomic
def create_issue(
    *,
    project,
    reporter,
    title,
    description,
    priority,
    assignee,
):
    locked_project = Project.objects.select_for_update().get(
        pk=project.pk,
    )

    issue_number = locked_project.next_issue_number

    issue = Issue.objects.create(
        project=locked_project,
        number=issue_number,
        title=title,
        description=description,
        priority=priority,
        reporter=reporter,
        assignee=assignee,
    )

    locked_project.next_issue_number += 1
    locked_project.save(
        update_fields=["next_issue_number"],
    )

    return issue


def update_issue_with_activity(*, issue, actor, form):
    old_issue = Issue.objects.select_related("assignee").get(pk=issue.pk)

    updated_issue = form.save()

    if old_issue.status != updated_issue.status:
        Activity.objects.create(
            issue=updated_issue,
            actor=actor,
            action="changed",
            field="status",
            old_value=old_issue.status,
            new_value=updated_issue.status,
        )

    if old_issue.priority != updated_issue.priority:
        Activity.objects.create(
            issue=updated_issue,
            actor=actor,
            action="changed",
            field="priority",
            old_value=old_issue.priority,
            new_value=updated_issue.priority,
        )

    if old_issue.assignee_id != updated_issue.assignee_id:
        Activity.objects.create(
            issue=updated_issue,
            actor=actor,
            action="changed",
            field="assignee",
            old_value=(old_issue.assignee.email if old_issue.assignee else ""),
            new_value=(updated_issue.assignee.email if updated_issue.assignee else ""),
        )

    return updated_issue


def create_comment_activity(*, issue, actor):
    return Activity.objects.create(
        issue=issue,
        actor=actor,
        action="commented",
    )
