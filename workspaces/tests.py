from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from workspaces.models import Workspace, WorkspaceMembership


class WorkspacePermissionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
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
            user=self.viewer,
            role=WorkspaceMembership.Role.VIEWER,
        )

    def test_owner_can_open_workspace_update_page(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "workspaces:update",
                kwargs={"slug": self.workspace.slug},
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_viewer_cannot_open_workspace_update_page(self):
        self.client.login(
            email="viewer@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "workspaces:update",
                kwargs={"slug": self.workspace.slug},
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(
            reverse(
                "workspaces:update",
                kwargs={"slug": self.workspace.slug},
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_user_sees_own_workspace_in_list(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(reverse("workspaces:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Workspace")

    def test_user_does_not_see_foreign_workspace_in_list(self):
        other_user = User.objects.create_user(
            email="other@example.com",
            password="TestPassword123!",
        )

        other_workspace = Workspace.objects.create(
            name="Other Workspace",
            slug="other-workspace",
        )

        WorkspaceMembership.objects.create(
            workspace=other_workspace,
            user=other_user,
            role=WorkspaceMembership.Role.OWNER,
        )

        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(reverse("workspaces:list"))

        self.assertNotContains(response, "Other Workspace")

    def test_user_cannot_open_foreign_workspace_detail(self):
        other_user = User.objects.create_user(
            email="other2@example.com",
            password="TestPassword123!",
        )

        other_workspace = Workspace.objects.create(
            name="Private Workspace",
            slug="private-workspace",
        )

        WorkspaceMembership.objects.create(
            workspace=other_workspace,
            user=other_user,
            role=WorkspaceMembership.Role.OWNER,
        )

        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "workspaces:detail",
                kwargs={"slug": other_workspace.slug},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_from_workspace_list(self):
        response = self.client.get(reverse("workspaces:list"))

        self.assertEqual(response.status_code, 302)
