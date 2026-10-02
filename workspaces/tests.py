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

    def test_workspace_member_can_open_member_list(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "workspaces:member-list",
                kwargs={"slug": self.workspace.slug},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "owner@example.com")
        self.assertContains(response, "viewer@example.com")

    def test_foreign_user_cannot_open_member_list(self):
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
            email="other@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "workspaces:member-list",
                kwargs={"slug": self.workspace.slug},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_can_add_workspace_member(self):
        new_user = User.objects.create_user(
            email="newuser@example.com",
            password="TestPassword123!",
        )

        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "workspaces:member-add",
                kwargs={"slug": self.workspace.slug},
            ),
            {
                "email": new_user.email,
                "role": WorkspaceMembership.Role.DEVELOPER,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            WorkspaceMembership.objects.filter(
                workspace=self.workspace,
                user=new_user,
                role=WorkspaceMembership.Role.DEVELOPER,
            ).exists()
        )

    def test_cannot_add_existing_workspace_member_again(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "workspaces:member-add",
                kwargs={"slug": self.workspace.slug},
            ),
            {
                "email": self.viewer.email,
                "role": WorkspaceMembership.Role.DEVELOPER,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "This user is already a workspace member.",
        )

    def test_manager_cannot_add_owner(self):
        manager = User.objects.create_user(
            email="manager@example.com",
            password="TestPassword123!",
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=manager,
            role=WorkspaceMembership.Role.MANAGER,
        )

        new_user = User.objects.create_user(
            email="newowner@example.com",
            password="TestPassword123!",
        )

        self.client.login(
            email="manager@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "workspaces:member-add",
                kwargs={"slug": self.workspace.slug},
            ),
            {
                "email": new_user.email,
                "role": WorkspaceMembership.Role.OWNER,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Only an owner can add another owner.",
        )

        self.assertFalse(
            WorkspaceMembership.objects.filter(
                workspace=self.workspace,
                user=new_user,
            ).exists()
        )

    def test_viewer_cannot_open_member_add_page(self):
        self.client.login(
            email="viewer@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "workspaces:member-add",
                kwargs={"slug": self.workspace.slug},
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_owner_can_change_member_role(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "workspaces:member-update",
                kwargs={
                    "slug": self.workspace.slug,
                    "membership_id": self.viewer.workspace_memberships.get(
                        workspace=self.workspace
                    ).id,
                },
            ),
            {
                "role": WorkspaceMembership.Role.DEVELOPER,
            },
        )

        self.assertEqual(response.status_code, 302)

        membership = WorkspaceMembership.objects.get(
            workspace=self.workspace,
            user=self.viewer,
        )

        self.assertEqual(
            membership.role,
            WorkspaceMembership.Role.DEVELOPER,
        )

    def test_manager_cannot_assign_owner_role(self):
        manager = User.objects.create_user(
            email="manager@example.com",
            password="TestPassword123!",
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=manager,
            role=WorkspaceMembership.Role.MANAGER,
        )

        self.client.login(
            email="manager@example.com",
            password="TestPassword123!",
        )

        viewer_membership = WorkspaceMembership.objects.get(
            workspace=self.workspace,
            user=self.viewer,
        )

        response = self.client.post(
            reverse(
                "workspaces:member-update",
                kwargs={
                    "slug": self.workspace.slug,
                    "membership_id": viewer_membership.id,
                },
            ),
            {
                "role": WorkspaceMembership.Role.OWNER,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Only an owner can assign the owner role.",
        )

        viewer_membership.refresh_from_db()

        self.assertEqual(
            viewer_membership.role,
            WorkspaceMembership.Role.VIEWER,
        )

    def test_last_owner_cannot_be_demoted(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        owner_membership = WorkspaceMembership.objects.get(
            workspace=self.workspace,
            user=self.owner,
        )

        response = self.client.post(
            reverse(
                "workspaces:member-update",
                kwargs={
                    "slug": self.workspace.slug,
                    "membership_id": owner_membership.id,
                },
            ),
            {
                "role": WorkspaceMembership.Role.MANAGER,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "The last owner cannot be demoted.",
        )

        owner_membership.refresh_from_db()

        self.assertEqual(
            owner_membership.role,
            WorkspaceMembership.Role.OWNER,
        )

    def test_owner_can_remove_developer(self):
        developer = User.objects.create_user(
            email="developer@example.com",
            password="TestPassword123!",
        )

        membership = WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=developer,
            role=WorkspaceMembership.Role.DEVELOPER,
        )

        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "workspaces:member-delete",
                kwargs={
                    "slug": self.workspace.slug,
                    "membership_id": membership.id,
                },
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            WorkspaceMembership.objects.filter(
                id=membership.id,
            ).exists()
        )

    def test_manager_cannot_remove_owner(self):
        manager = User.objects.create_user(
            email="manager@example.com",
            password="TestPassword123!",
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=manager,
            role=WorkspaceMembership.Role.MANAGER,
        )

        owner_membership = WorkspaceMembership.objects.get(
            workspace=self.workspace,
            user=self.owner,
        )

        self.client.login(
            email="manager@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "workspaces:member-delete",
                kwargs={
                    "slug": self.workspace.slug,
                    "membership_id": owner_membership.id,
                },
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            WorkspaceMembership.objects.filter(
                id=owner_membership.id,
            ).exists()
        )

    def test_last_owner_cannot_remove_self(self):
        owner_membership = WorkspaceMembership.objects.get(
            workspace=self.workspace,
            user=self.owner,
        )

        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "workspaces:member-delete",
                kwargs={
                    "slug": self.workspace.slug,
                    "membership_id": owner_membership.id,
                },
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            WorkspaceMembership.objects.filter(
                id=owner_membership.id,
            ).exists()
        )
