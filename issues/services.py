from django.db import transaction

from projects.models import Project

from .models import Issue


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
