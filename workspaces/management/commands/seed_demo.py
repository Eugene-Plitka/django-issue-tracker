import os

from django.conf import settings
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from issues.models import Activity, Comment, Issue, Label
from issues.services import create_comment_activity, create_issue
from projects.models import Project, ProjectMembership
from workspaces.models import Workspace, WorkspaceMembership

DEMO_PASSWORD = os.environ.get("DEMO_USER_PASSWORD", "test12345")

DEMO_USERS = {
    "owner@example.com": WorkspaceMembership.Role.OWNER,
    "manager@example.com": WorkspaceMembership.Role.MANAGER,
    "developer@example.com": WorkspaceMembership.Role.DEVELOPER,
    "viewer@example.com": WorkspaceMembership.Role.VIEWER,
}


class Command(BaseCommand):
    help = "Reset the database to a portfolio-ready demo data set."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not os.environ.get("DEMO_USER_PASSWORD"):
            raise ValueError("DEMO_USER_PASSWORD is required in production.")

        self.stdout.write("Removing existing demo workspaces...")

        Workspace.objects.all().delete()

        users = self._prepare_users()

        self.stdout.write("Creating demo workspaces...")

        commerce_workspace = self._create_commerce_workspace(users)
        platform_workspace = self._create_platform_workspace(users)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Demo data created successfully.",
            )
        )
        self.stdout.write("")
        self.stdout.write("Demo users:")
        self.stdout.write("  owner@example.com")
        self.stdout.write("  manager@example.com")
        self.stdout.write("  developer@example.com")
        self.stdout.write("  viewer@example.com")
        self.stdout.write(f"Password for all users: {DEMO_PASSWORD}")
        self.stdout.write("")
        self.stdout.write(
            f"Workspaces created: {commerce_workspace.name}, {platform_workspace.name}"
        )

    def _prepare_users(self):
        users = {}

        for email in DEMO_USERS:
            user, _ = User.objects.get_or_create(
                email=email,
            )

            user.set_password(DEMO_PASSWORD)
            user.is_active = True
            user.is_staff = False
            user.is_superuser = False
            user.user_permissions.clear()
            user.groups.clear()
            user.save(
                update_fields=[
                    "password",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ]
            )

            users[email] = user

        return users

    def _add_workspace_members(self, workspace, users):
        for email, role in DEMO_USERS.items():
            WorkspaceMembership.objects.create(
                workspace=workspace,
                user=users[email],
                role=role,
            )

    def _add_project_members(
        self,
        project,
        users,
        *,
        include_developer=True,
        include_viewer=True,
    ):
        if include_developer:
            ProjectMembership.objects.create(
                project=project,
                user=users["developer@example.com"],
            )

        if include_viewer:
            ProjectMembership.objects.create(
                project=project,
                user=users["viewer@example.com"],
            )

    def _create_labels(self, project, names):
        return {
            name: Label.objects.create(
                project=project,
                name=name,
            )
            for name in names
        }

    def _create_demo_issue(
        self,
        *,
        project,
        reporter,
        title,
        description,
        priority,
        assignee,
        status,
        labels,
        comments,
        age_days,
    ):
        issue = create_issue(
            project=project,
            reporter=reporter,
            title=title,
            description=description,
            priority=priority,
            assignee=assignee,
        )

        issue.labels.set(labels)

        if status != Issue.Status.TODO:
            old_status = issue.status

            issue.status = status
            issue.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            Activity.objects.create(
                issue=issue,
                actor=assignee or reporter,
                action="changed",
                field="status",
                old_value=old_status,
                new_value=status,
            )

        for author, body in comments:
            Comment.objects.create(
                issue=issue,
                author=author,
                body=body,
            )

            create_comment_activity(
                issue=issue,
                actor=author,
            )

        self._shift_issue_timestamps(
            issue=issue,
            age_days=age_days,
        )

        return issue

    def _shift_issue_timestamps(self, *, issue, age_days):
        created_at = timezone.now() - timedelta(days=age_days)

        Issue.objects.filter(pk=issue.pk).update(
            created_at=created_at,
            updated_at=created_at + timedelta(hours=6),
        )

        comments = list(
            issue.comments.order_by("pk"),
        )

        for index, comment in enumerate(comments, start=1):
            timestamp = created_at + timedelta(
                hours=8 + index,
            )

            Comment.objects.filter(pk=comment.pk).update(
                created_at=timestamp,
                updated_at=timestamp,
            )

        activities = list(
            issue.activities.order_by("pk"),
        )

        for index, activity in enumerate(activities, start=1):
            Activity.objects.filter(pk=activity.pk).update(
                created_at=created_at
                + timedelta(
                    hours=index * 2,
                )
            )

    def _create_commerce_workspace(self, users):
        owner = users["owner@example.com"]
        manager = users["manager@example.com"]
        developer = users["developer@example.com"]
        viewer = users["viewer@example.com"]

        workspace = Workspace.objects.create(
            name="Northstar Commerce",
            slug="northstar-commerce",
        )

        self._add_workspace_members(
            workspace,
            users,
        )

        storefront = Project.objects.create(
            workspace=workspace,
            name="Customer Storefront",
            key="WEB",
            description=(
                "Customer-facing storefront covering product discovery, "
                "checkout, account pages, and responsive user experience."
            ),
        )

        backend = Project.objects.create(
            workspace=workspace,
            name="Commerce API",
            key="API",
            description=(
                "Backend services for catalog, checkout, orders, payments, "
                "and integrations with external systems."
            ),
        )

        self._add_project_members(
            storefront,
            users,
        )

        self._add_project_members(
            backend,
            users,
        )

        storefront_labels = self._create_labels(
            storefront,
            [
                "frontend",
                "bug",
                "ux",
                "performance",
                "accessibility",
            ],
        )

        backend_labels = self._create_labels(
            backend,
            [
                "backend",
                "bug",
                "api",
                "security",
                "performance",
            ],
        )

        self._create_demo_issue(
            project=storefront,
            reporter=manager,
            title="Improve mobile checkout layout",
            description=(
                "The checkout summary becomes difficult to scan on narrow "
                "screens. Rework the layout so delivery details, totals, and "
                "the payment action remain readable on mobile devices."
            ),
            priority=Issue.Priority.HIGH,
            assignee=developer,
            status=Issue.Status.IN_PROGRESS,
            labels=[
                storefront_labels["frontend"],
                storefront_labels["ux"],
            ],
            comments=[
                (
                    manager,
                    "The largest drop-off is currently on screens below 390px.",
                ),
                (
                    developer,
                    "I reproduced the issue and started restructuring the "
                    "checkout grid.",
                ),
            ],
            age_days=12,
        )

        self._create_demo_issue(
            project=storefront,
            reporter=owner,
            title="Add accessible labels to checkout form",
            description=(
                "Review checkout form controls and ensure all interactive "
                "elements have accessible names and useful validation text."
            ),
            priority=Issue.Priority.MEDIUM,
            assignee=developer,
            status=Issue.Status.DONE,
            labels=[
                storefront_labels["accessibility"],
                storefront_labels["frontend"],
            ],
            comments=[
                (
                    viewer,
                    "Verified the updated form with keyboard-only navigation.",
                ),
            ],
            age_days=20,
        )

        self._create_demo_issue(
            project=storefront,
            reporter=manager,
            title="Product image gallery loads slowly",
            description=(
                "Large product galleries cause noticeable delays on first "
                "load. Investigate image loading strategy and unnecessary "
                "requests."
            ),
            priority=Issue.Priority.MEDIUM,
            assignee=None,
            status=Issue.Status.TODO,
            labels=[
                storefront_labels["performance"],
            ],
            comments=[
                (
                    viewer,
                    "This is especially visible on product pages with more "
                    "than eight images.",
                ),
            ],
            age_days=5,
        )

        self._create_demo_issue(
            project=backend,
            reporter=manager,
            title="Prevent duplicate order submission",
            description=(
                "Repeated checkout requests can create duplicate orders when "
                "the client retries after a slow response. Introduce an "
                "idempotency strategy for order creation."
            ),
            priority=Issue.Priority.CRITICAL,
            assignee=developer,
            status=Issue.Status.IN_PROGRESS,
            labels=[
                backend_labels["backend"],
                backend_labels["bug"],
                backend_labels["api"],
            ],
            comments=[
                (
                    manager,
                    "We reproduced this with two requests sent within the same second.",
                ),
                (
                    developer,
                    "I am testing an idempotency key stored against the order request.",
                ),
            ],
            age_days=8,
        )

        self._create_demo_issue(
            project=backend,
            reporter=owner,
            title="Audit order endpoint permissions",
            description=(
                "Review authorization checks for order detail and update "
                "endpoints to ensure customers can only access their own "
                "orders."
            ),
            priority=Issue.Priority.HIGH,
            assignee=manager,
            status=Issue.Status.DONE,
            labels=[
                backend_labels["security"],
                backend_labels["api"],
            ],
            comments=[
                (
                    manager,
                    "Object-level checks are now covered by regression tests.",
                ),
                (
                    viewer,
                    "Reviewed the final behavior from the customer account.",
                ),
            ],
            age_days=27,
        )

        self._create_demo_issue(
            project=backend,
            reporter=developer,
            title="Reduce catalog endpoint query count",
            description=(
                "The catalog list performs repeated category and manufacturer "
                "queries. Inspect ORM usage and remove the current N+1 query "
                "pattern."
            ),
            priority=Issue.Priority.MEDIUM,
            assignee=developer,
            status=Issue.Status.TODO,
            labels=[
                backend_labels["performance"],
                backend_labels["backend"],
            ],
            comments=[],
            age_days=3,
        )

        return workspace

    def _create_platform_workspace(self, users):
        owner = users["owner@example.com"]
        manager = users["manager@example.com"]
        developer = users["developer@example.com"]
        viewer = users["viewer@example.com"]

        workspace = Workspace.objects.create(
            name="Atlas Internal Platform",
            slug="atlas-internal-platform",
        )

        self._add_workspace_members(
            workspace,
            users,
        )

        operations = Project.objects.create(
            workspace=workspace,
            name="Operations Dashboard",
            key="OPS",
            description=(
                "Internal dashboard used by support and operations teams for "
                "monitoring customer accounts and operational workflows."
            ),
        )

        delivery = Project.objects.create(
            workspace=workspace,
            name="Release & Delivery",
            key="REL",
            description=(
                "Deployment, CI, release management, observability, and "
                "production-readiness work."
            ),
        )

        self._add_project_members(
            operations,
            users,
        )

        self._add_project_members(
            delivery,
            users,
            include_viewer=False,
        )

        operations_labels = self._create_labels(
            operations,
            [
                "dashboard",
                "bug",
                "feature",
                "support",
                "ux",
            ],
        )

        delivery_labels = self._create_labels(
            delivery,
            [
                "devops",
                "ci",
                "deployment",
                "monitoring",
                "documentation",
            ],
        )

        self._create_demo_issue(
            project=operations,
            reporter=manager,
            title="Add account health summary",
            description=(
                "Add a compact account health section showing recent errors, "
                "open support cases, and the latest successful synchronization."
            ),
            priority=Issue.Priority.HIGH,
            assignee=developer,
            status=Issue.Status.IN_PROGRESS,
            labels=[
                operations_labels["feature"],
                operations_labels["dashboard"],
            ],
            comments=[
                (
                    manager,
                    "Support asked for this information to be visible without "
                    "opening several separate pages.",
                ),
                (
                    developer,
                    "The first version of the summary component is ready for review.",
                ),
            ],
            age_days=14,
        )

        self._create_demo_issue(
            project=operations,
            reporter=viewer,
            title="Filters reset after returning from account detail",
            description=(
                "When a user opens an account and then returns to the list, "
                "the previously selected filters are lost."
            ),
            priority=Issue.Priority.MEDIUM,
            assignee=developer,
            status=Issue.Status.TODO,
            labels=[
                operations_labels["bug"],
                operations_labels["ux"],
            ],
            comments=[
                (
                    viewer,
                    "This slows down support work when reviewing a group of "
                    "accounts with the same filter.",
                ),
            ],
            age_days=4,
        )

        self._create_demo_issue(
            project=operations,
            reporter=owner,
            title="Clarify suspended account state",
            description=(
                "Improve the wording and visual state used for suspended "
                "accounts so support agents do not confuse suspension with "
                "account deletion."
            ),
            priority=Issue.Priority.LOW,
            assignee=manager,
            status=Issue.Status.DONE,
            labels=[
                operations_labels["support"],
                operations_labels["ux"],
            ],
            comments=[
                (
                    viewer,
                    "The updated wording is much clearer during support calls.",
                ),
            ],
            age_days=31,
        )

        self._create_demo_issue(
            project=delivery,
            reporter=owner,
            title="Add deployment smoke-check checklist",
            description=(
                "Document a short post-deployment checklist covering login, "
                "workspace access, issue creation, static assets, and database "
                "connectivity."
            ),
            priority=Issue.Priority.MEDIUM,
            assignee=manager,
            status=Issue.Status.DONE,
            labels=[
                delivery_labels["deployment"],
                delivery_labels["documentation"],
            ],
            comments=[
                (
                    manager,
                    "The checklist is now part of the release routine.",
                ),
            ],
            age_days=18,
        )

        self._create_demo_issue(
            project=delivery,
            reporter=manager,
            title="Track CI duration regression",
            description=(
                "CI runtime has increased noticeably. Identify the slowest "
                "steps and determine whether test execution or dependency "
                "installation is responsible."
            ),
            priority=Issue.Priority.MEDIUM,
            assignee=developer,
            status=Issue.Status.IN_PROGRESS,
            labels=[
                delivery_labels["ci"],
                delivery_labels["monitoring"],
            ],
            comments=[
                (
                    developer,
                    "Most of the increase currently comes from the test suite, "
                    "not dependency installation.",
                ),
            ],
            age_days=7,
        )

        self._create_demo_issue(
            project=delivery,
            reporter=developer,
            title="Document rollback procedure",
            description=(
                "Create a concise rollback procedure for a failed release, "
                "including application image rollback and database migration "
                "considerations."
            ),
            priority=Issue.Priority.HIGH,
            assignee=developer,
            status=Issue.Status.TODO,
            labels=[
                delivery_labels["deployment"],
                delivery_labels["documentation"],
            ],
            comments=[],
            age_days=2,
        )

        return workspace
