from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from projects.models import Project, ProjectMembership
from workspaces.models import Workspace, WorkspaceMembership


class ProjectListTests(TestCase):
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

    def test_owner_sees_all_workspace_projects(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "projects:list",
                kwargs={"workspace_slug": self.workspace.slug},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Backend API")

    def test_developer_does_not_see_project_without_membership(self):
        self.client.login(
            email="developer@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "projects:list",
                kwargs={"workspace_slug": self.workspace.slug},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Backend API")

    def test_developer_sees_project_with_membership(self):
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
                "projects:list",
                kwargs={"workspace_slug": self.workspace.slug},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Backend API")
