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
