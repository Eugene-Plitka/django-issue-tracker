from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from issues.models import Activity, Comment, Issue, Label
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

    def test_issue_creation_creates_activity(self):
        project = Project.objects.create(
            workspace=self.workspace,
            name="Activity Project",
            key="ACT",
        )

        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "issues:create",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": project.key,
                },
            ),
            {
                "title": "Created issue",
                "description": "",
                "priority": Issue.Priority.MEDIUM,
                "assignee": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        issue = Issue.objects.get(
            project=project,
            title="Created issue",
        )

        activity = Activity.objects.get(
            issue=issue,
            action="created",
        )

        self.assertEqual(activity.actor, self.owner)


class IssueCommentTests(TestCase):
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

        self.project = Project.objects.create(
            workspace=self.workspace,
            name="Backend",
            key="BACK",
        )

        ProjectMembership.objects.create(
            project=self.project,
            user=self.viewer,
        )

        self.issue = Issue.objects.create(
            project=self.project,
            number=1,
            title="Test issue",
            reporter=self.owner,
        )

    def test_owner_can_add_comment(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "issues:detail",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "issue_number": self.issue.number,
                },
            ),
            {
                "body": "Test comment",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Comment.objects.filter(
                issue=self.issue,
                author=self.owner,
                body="Test comment",
            ).exists()
        )

    def test_viewer_cannot_add_comment(self):
        self.client.login(
            email="viewer@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "issues:detail",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "issue_number": self.issue.number,
                },
            ),
            {
                "body": "Viewer comment",
            },
        )

        self.assertEqual(response.status_code, 403)

        self.assertFalse(
            Comment.objects.filter(
                issue=self.issue,
                author=self.viewer,
            ).exists()
        )

    def test_comment_is_displayed_on_issue_detail(self):
        Comment.objects.create(
            issue=self.issue,
            author=self.owner,
            body="Visible comment",
        )

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

        self.assertContains(response, "Visible comment")

    def test_comment_creates_activity(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        self.client.post(
            reverse(
                "issues:detail",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                    "issue_number": self.issue.number,
                },
            ),
            {
                "body": "New comment",
            },
        )

        activity = Activity.objects.get(
            issue=self.issue,
            action="commented",
        )

        self.assertEqual(activity.actor, self.owner)


class LabelTests(TestCase):
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

        ProjectMembership.objects.create(
            project=self.project,
            user=self.developer,
        )

    def test_owner_can_open_label_list(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "issues:label-list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_developer_can_open_label_list(self):
        self.client.login(
            email="developer@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "issues:label-list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_owner_can_create_label(self):
        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "issues:label-create",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "name": "bug",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Label.objects.filter(
                project=self.project,
                name="bug",
            ).exists()
        )

    def test_developer_cannot_create_label(self):
        self.client.login(
            email="developer@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "issues:label-create",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "name": "bug",
            },
        )

        self.assertEqual(response.status_code, 403)

        self.assertFalse(
            Label.objects.filter(
                project=self.project,
                name="bug",
            ).exists()
        )

    def test_developer_without_project_access_cannot_open_label_list(self):
        other_developer = User.objects.create_user(
            email="other@example.com",
            password="TestPassword123!",
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=other_developer,
            role=WorkspaceMembership.Role.DEVELOPER,
        )

        self.client.login(
            email="other@example.com",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "issues:label-list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            )
        )

        self.assertEqual(response.status_code, 404)


class IssueFilterTests(TestCase):
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

        ProjectMembership.objects.create(
            project=self.project,
            user=self.developer,
        )

        self.bug_label = Label.objects.create(
            project=self.project,
            name="bug",
        )

        self.feature_label = Label.objects.create(
            project=self.project,
            name="feature",
        )

        self.issue_one = Issue.objects.create(
            project=self.project,
            number=1,
            title="First issue",
            reporter=self.owner,
            assignee=self.developer,
            status=Issue.Status.TODO,
            priority=Issue.Priority.HIGH,
        )

        self.issue_two = Issue.objects.create(
            project=self.project,
            number=2,
            title="Second issue",
            reporter=self.owner,
            status=Issue.Status.DONE,
            priority=Issue.Priority.LOW,
        )

        self.issue_one.labels.add(self.bug_label)
        self.issue_two.labels.add(self.feature_label)

        self.client.login(
            email="owner@example.com",
            password="TestPassword123!",
        )

    def test_filter_issues_by_status(self):
        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "status": Issue.Status.TODO,
            },
        )

        self.assertContains(response, "First issue")
        self.assertNotContains(response, "Second issue")

    def test_filter_issues_by_priority(self):
        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "priority": Issue.Priority.LOW,
            },
        )

        self.assertContains(response, "Second issue")
        self.assertNotContains(response, "First issue")

    def test_filter_issues_by_assignee(self):
        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "assignee": str(self.developer.id),
            },
        )

        self.assertContains(response, "First issue")
        self.assertNotContains(response, "Second issue")

    def test_filter_issues_by_label(self):
        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "label": str(self.bug_label.id),
            },
        )

        self.assertContains(response, "First issue")
        self.assertNotContains(response, "Second issue")

    def test_filter_issues_by_status_and_priority(self):
        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "status": Issue.Status.TODO,
                "priority": Issue.Priority.HIGH,
            },
        )

        self.assertContains(response, "First issue")
        self.assertNotContains(response, "Second issue")

    def test_search_issues_by_title(self):
        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "q": "First",
            },
        )

        self.assertContains(response, "First issue")
        self.assertNotContains(response, "Second issue")

    def test_search_issues_by_project_key(self):
        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "q": "back",
            },
        )

        self.assertContains(response, "First issue")
        self.assertContains(response, "Second issue")

    def test_search_issue_by_full_key(self):
        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "q": "BACK-1",
            },
        )

        self.assertContains(response, "First issue")
        self.assertNotContains(response, "Second issue")

    def test_search_issue_by_full_key_is_case_insensitive(self):
        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "q": "back-1",
            },
        )

        self.assertContains(response, "First issue")
        self.assertNotContains(response, "Second issue")

    def test_sort_issues_by_priority(self):
        self.issue_one.priority = Issue.Priority.LOW
        self.issue_one.save()

        self.issue_two.priority = Issue.Priority.CRITICAL
        self.issue_two.save()

        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "sort": "priority",
            },
        )

        issues = list(response.context["issues"])

        self.assertEqual(
            issues[0],
            self.issue_two,
        )
        self.assertEqual(
            issues[1],
            self.issue_one,
        )

    def test_sort_issues_by_updated(self):
        self.issue_one.title = "Updated issue"
        self.issue_one.save()

        response = self.client.get(
            reverse(
                "issues:list",
                kwargs={
                    "workspace_slug": self.workspace.slug,
                    "project_key": self.project.key,
                },
            ),
            {
                "sort": "updated",
            },
        )

        issues = list(response.context["issues"])

        self.assertEqual(
            issues[0],
            self.issue_one,
        )
