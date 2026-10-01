from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from issues.models import Activity, Issue
from projects.models import Project, ProjectMembership
from workspaces.models import Workspace, WorkspaceMembership


class IssueListTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="TestPassword123!",
        )

        self.developer = User.objects.create_user(
            email="developer@example.com",
            password="TestPassword123!",
        )

        self.workspace = Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace",
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.owner,
            role=WorkspaceMembership.Role.OWNER,
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.developer,
            role=WorkspaceMembership.Role.DEVELOPER,
        )

        self.project = Project.objects.create(
            workspace=self.workspace,
            name="Backend API",
            key="BACK",
        )

        self.issue = Issue.objects.create(
            project=self.project,
            number=1,
            title="Test issue",
            reporter=self.owner,
        )

    def test_owner_can_open_issue_list(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test issue")

    def test_developer_without_project_membership_cannot_open_issue_list(self):
        self.client.login(
            email="developer@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_developer_with_project_membership_can_open_issue_list(self):
        ProjectMembership.objects.create(
            project=self.project,
            user=self.developer,
        )

        self.client.login(
            email="developer@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test issue")


class IssueCreateTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="TestPassword123!",
        )
        self.developer = User.objects.create_user(
            email="developer@example.com",
            password="TestPassword123!",
        )
        self.viewer = User.objects.create_user(
            email="viewer@example.com",
            password="TestPassword123!",
        )

        self.workspace = Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace",
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.owner,
            role=WorkspaceMembership.Role.OWNER,
        )
        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.developer,
            role=WorkspaceMembership.Role.DEVELOPER,
        )
        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.viewer,
            role=WorkspaceMembership.Role.VIEWER,
        )

        self.project = Project.objects.create(
            workspace=self.workspace,
            name="Backend",
            key="BACK",
        )

        ProjectMembership.objects.create(
            project=self.project,
            user=self.developer,
        )
        ProjectMembership.objects.create(
            project=self.project,
            user=self.viewer,
        )

    def test_owner_can_create_issue_with_automatic_number(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "issues:create",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "title": "First issue",
                "description": "",
                "priority": Issue.Priority.MEDIUM,
                "assignee": self.developer.id,
            },
        )

        self.assertEqual(response.status_code, 302)

        issue = Issue.objects.get(
            project=self.project,
            title="First issue",
        )

        self.assertEqual(issue.number, 1)

        self.project.refresh_from_db()

        self.assertEqual(
            self.project.next_issue_number,
            2,
        )

    def test_issue_numbers_increment(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        url = reverse(
            "issues:create",
            kwargs={
                "workspace_slug": self.workspace.slug,
                "project_key": self.project.key,
            },
        )

        self.client.post(
            url,
            {
                "title": "First issue",
                "description": "",
                "priority": Issue.Priority.MEDIUM,
                "assignee": "",
            },
        )

        self.client.post(
            url,
            {
                "title": "Second issue",
                "description": "",
                "priority": Issue.Priority.HIGH,
                "assignee": "",
            },
        )

        numbers = list(
            Issue.objects.filter(
                project=self.project,
            )
            .order_by("number")
            .values_list("number", flat=True)
        )

        self.assertEqual(numbers, [1, 2])

    def test_viewer_cannot_create_issue(self):
        self.client.login(
            email="viewer@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "issues:create",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 403)


class IssueDetailTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="TestPassword123!",
        )
        self.developer = User.objects.create_user(
            email="developer@example.com",
            password="TestPassword123!",
        )

        self.workspace = Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace",
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.owner,
            role=WorkspaceMembership.Role.OWNER,
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.developer,
            role=WorkspaceMembership.Role.DEVELOPER,
        )

        self.project = Project.objects.create(
            workspace=self.workspace,
            name="Backend",
            key="BACK",
        )

        self.issue = Issue.objects.create(
            project=self.project,
            number=1,
            title="Test issue",
            reporter=self.owner,
        )

    def test_owner_can_open_issue_detail(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "issues:detail",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "issue_number": self.issue.number,
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test issue")

    def test_developer_with_project_membership_can_open_issue_detail(self):
        ProjectMembership.objects.create(
            project=self.project,
            user=self.developer,
        )

        self.client.login(
            email="developer@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "issues:detail",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "issue_number": self.issue.number,
                },
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_developer_without_project_membership_cannot_open_issue_detail(self):
        self.client.login(
            email="developer@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "issues:detail",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "issue_number": self.issue.number,
                },
            )
        )

        self.assertEqual(response.status_code, 404)


class IssueUpdateTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="TestPassword123!",
        )
        self.developer = User.objects.create_user(
            email="developer@example.com",
            password="TestPassword123!",
        )
        self.viewer = User.objects.create_user(
            email="viewer@example.com",
            password="TestPassword123!",
        )

        self.workspace = Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace",
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.owner,
            role=WorkspaceMembership.Role.OWNER,
        )
        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.developer,
            role=WorkspaceMembership.Role.DEVELOPER,
        )
        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.viewer,
            role=WorkspaceMembership.Role.VIEWER,
        )

        self.project = Project.objects.create(
            workspace=self.workspace,
            name="Backend",
            key="BACK",
        )

        ProjectMembership.objects.create(
            project=self.project,
            user=self.developer,
        )
        ProjectMembership.objects.create(
            project=self.project,
            user=self.viewer,
        )

        self.issue = Issue.objects.create(
            project=self.project,
            number=1,
            title="Original title",
            description="Original description",
            reporter=self.owner,
            priority=Issue.Priority.MEDIUM,
        )

    def test_owner_can_update_priority(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "issues:update",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "issue_number": self.issue.number,
                },
            ),
            {
                "title": self.issue.title,
                "description": self.issue.description,
                "status": Issue.Status.TODO,
                "priority": Issue.Priority.HIGH,
                "assignee": "",
                "labels": [],
            },
        )

        self.assertEqual(response.status_code, 302)

        self.issue.refresh_from_db()

        self.assertEqual(
            self.issue.priority,
            Issue.Priority.HIGH,
        )

    def test_developer_cannot_change_title_of_foreign_issue(self):
        self.client.login(
            email="developer@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "issues:update",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "issue_number": self.issue.number,
                },
            ),
            {
                "title": "Hacked title",
                "description": "Changed",
                "status": Issue.Status.IN_PROGRESS,
                "labels": [],
                "assign_to_me": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.issue.refresh_from_db()

        self.assertEqual(
            self.issue.title,
            "Original title",
        )

        self.assertEqual(
            self.issue.status,
            Issue.Status.IN_PROGRESS,
        )

    def test_developer_can_assign_issue_to_self(self):
        self.client.login(
            email="developer@example.com",
            password="TestPassword123!",
        )

        self.client.post(
            reverse(
                "issues:update",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "issue_number": self.issue.number,
                },
            ),
            {
                "status": Issue.Status.TODO,
                "labels": [],
                "assign_to_me": "on",
            },
        )

        self.issue.refresh_from_db()

        self.assertEqual(
            self.issue.assignee,
            self.developer,
        )

    def test_viewer_cannot_open_issue_update_page(self):
        self.client.login(
            email="viewer@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "issues:update",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "issue_number": self.issue.number,
                },
            )
        )

        self.assertEqual(response.status_code, 403)


class IssueActivityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="TestPassword123!",
        )

        self.workspace = Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace",
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.owner,
            role=WorkspaceMembership.Role.OWNER,
        )

        self.project = Project.objects.create(
            workspace=self.workspace,
            name="Backend",
            key="BACK",
        )

        self.issue = Issue.objects.create(
            project=self.project,
            number=1,
            title="Test issue",
            reporter=self.owner,
            status=Issue.Status.TODO,
            priority=Issue.Priority.MEDIUM,
        )

    def test_status_change_creates_activity(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        self.client.post(
            reverse(
                "issues:update",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "issue_number": self.issue.number,
                },
            ),
            {
                "title": self.issue.title,
                "description": "",
                "status": Issue.Status.IN_PROGRESS,
                "priority": Issue.Priority.MEDIUM,
                "assignee": "",
                "labels": [],
            },
        )

        activity = Activity.objects.get(
            issue=self.issue,
            field="status",
        )

        self.assertEqual(
            activity.old_value,
            Issue.Status.TODO,
        )
        self.assertEqual(
            activity.new_value,
            Issue.Status.IN_PROGRESS,
        )
        self.assertEqual(
            activity.actor,
            self.owner,
        )

    def test_unchanged_status_does_not_create_activity(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        self.client.post(
            reverse(
                "issues:update",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "issue_number": self.issue.number,
                },
            ),
            {
                "title": self.issue.title,
                "description": "",
                "status": Issue.Status.TODO,
                "priority": Issue.Priority.MEDIUM,
                "assignee": "",
                "labels": [],
            },
        )

        self.assertFalse(
            Activity.objects.filter(
                issue=self.issue,
                field="status",
            ).exists()
        )

    def test_multiple_field_changes_create_multiple_activities(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        self.client.post(
            reverse(
                "issues:update",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "issue_number": self.issue.number,
                },
            ),
            {
                "title": self.issue.title,
                "description": "",
                "status": Issue.Status.DONE,
                "priority": Issue.Priority.HIGH,
                "assignee": "",
                "labels": [],
            },
        )

        self.assertEqual(
            Activity.objects.filter(
                issue=self.issue,
            ).count(),
            2,
        )
