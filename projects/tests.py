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

    def test_owner_can_create_project(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "projects:create",
                kwargs={"workspace_slug": self.workspace.slug},
            ),
            {
                "name": "Frontend",
                "key": "WEB",
                "description": "Frontend application",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Project.objects.filter(
                workspace=self.workspace,
                key="WEB",
                name="Frontend",
            ).exists()
        )

    def test_manager_can_create_project(self):
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

        response = self.client.post(
            reverse(
                "projects:create",
                kwargs={"workspace_slug": self.workspace.slug},
            ),
            {
                "name": "Frontend",
                "key": "WEB",
                "description": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Project.objects.filter(
                workspace=self.workspace,
                key="WEB",
            ).exists()
        )

    def test_developer_cannot_open_project_create_page(self):
        self.client.login(
            email="developer@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "projects:create",
                kwargs={"workspace_slug": self.workspace.slug},
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_owner_can_open_project_detail(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "projects:detail",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Backend API")

    def test_developer_with_membership_can_open_project_detail(self):
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
                "projects:detail",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_developer_without_membership_cannot_open_project_detail(self):
        self.client.login(
            email="developer@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "projects:detail",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_can_open_project_member_list(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "projects:member-list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_developer_with_membership_can_open_project_member_list(self):
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
                "projects:member-list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_developer_without_membership_cannot_open_project_member_list(self):
        self.client.login(
            email="developer@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "projects:member-list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_can_add_project_member(self):
        ProjectMembership.objects.all().delete()

        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "projects:member-add",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "user": self.developer.id,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            ProjectMembership.objects.filter(
                project=self.project,
                user=self.developer,
            ).exists()
        )

    def test_developer_cannot_open_project_member_add_page(self):
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
                "projects:member-add",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_project_member_form_excludes_users_outside_workspace(self):
        outside_user = User.objects.create_user(
            email="outside@example.com",
            password="TestPassword123!",
        )

        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "projects:member-add",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        form = response.context["form"]

        self.assertNotIn(
            outside_user,
            form.fields["user"].queryset,
        )

    def test_project_member_form_excludes_existing_project_members(self):
        ProjectMembership.objects.create(
            project=self.project,
            user=self.developer,
        )

        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "projects:member-add",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        form = response.context["form"]

        self.assertNotIn(
            self.developer,
            form.fields["user"].queryset,
        )

    def test_owner_can_remove_project_member(self):
        membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.developer,
        )

        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "projects:member-delete",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "membership_id": membership.id,
                },
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            ProjectMembership.objects.filter(
                id=membership.id,
            ).exists()
        )

    def test_developer_cannot_remove_project_member(self):
        ProjectMembership.objects.create(
            project=self.project,
            user=self.developer,
        )

        other_user = User.objects.create_user(
            email="other@example.com",
            password="TestPassword123!",
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=other_user,
            role=WorkspaceMembership.Role.DEVELOPER,
        )

        other_membership = ProjectMembership.objects.create(
            project=self.project,
            user=other_user,
        )

        self.client.login(
            email="developer@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "projects:member-delete",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "membership_id": other_membership.id,
                },
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            ProjectMembership.objects.filter(
                id=other_membership.id,
            ).exists()
        )

    def test_removing_project_member_keeps_workspace_membership(self):
        membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.developer,
        )

        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        self.client.post(
            reverse(
                "projects:member-delete",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "membership_id": membership.id,
                },
            )
        )

        self.assertTrue(
            WorkspaceMembership.objects.filter(
                workspace=self.workspace,
                user=self.developer,
            ).exists()
        )

    def test_owner_can_update_project(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "projects:update",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "name": "Backend Service",
                "key": "API",
                "description": "Updated description",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.project.refresh_from_db()

        self.assertEqual(self.project.name, "Backend Service")
        self.assertEqual(self.project.key, "API")

    def test_manager_can_update_project(self):
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

        response = self.client.post(
            reverse(
                "projects:update",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "name": "Updated Backend",
                "key": self.project.key,
                "description": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.project.refresh_from_db()

        self.assertEqual(
            self.project.name,
            "Updated Backend",
        )

    def test_developer_cannot_update_project(self):
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
                "projects:update",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 403)
