from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from issues.models import Issue
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
