# Create your tests here.
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from workspaces.models import WorkspaceMembership

User = get_user_model()


class AccountSignupTests(TestCase):
    def test_signup_page_is_available(self):
        response = self.client.get(reverse("account_signup"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/signup.html")

    def test_user_can_sign_up_with_email_and_password(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "email": "newuser@example.com",
                "password1": "StrongTestPassword123!",
                "password2": "StrongTestPassword123!",
            },
        )

        self.assertEqual(response.status_code, 302)

        user = User.objects.get(email="newuser@example.com")

        self.assertTrue(user.check_password("StrongTestPassword123!"))
        self.assertNotIn("_auth_user_id", {})

    def test_signup_logs_user_in(self):
        self.client.post(
            reverse("account_signup"),
            {
                "email": "newuser@example.com",
                "password1": "StrongTestPassword123!",
                "password2": "StrongTestPassword123!",
            },
        )

        user = User.objects.get(email="newuser@example.com")

        self.assertEqual(
            str(self.client.session["_auth_user_id"]),
            str(user.pk),
        )

    def test_signup_does_not_create_workspace_membership(self):
        self.client.post(
            reverse("account_signup"),
            {
                "email": "newuser@example.com",
                "password1": "StrongTestPassword123!",
                "password2": "StrongTestPassword123!",
            },
        )

        user = User.objects.get(email="newuser@example.com")

        self.assertFalse(WorkspaceMembership.objects.filter(user=user).exists())

    def test_signup_rejects_duplicate_email(self):
        User.objects.create_user(
            email="existing@example.com",
            password="StrongTestPassword123!",
        )

        response = self.client.post(
            reverse("account_signup"),
            {
                "email": "existing@example.com",
                "password1": "AnotherStrongPassword123!",
                "password2": "AnotherStrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            User.objects.filter(email="existing@example.com").count(),
            1,
        )


class AccountLoginTests(TestCase):
    def setUp(self):
        self.password = "StrongTestPassword123!"
        self.user = User.objects.create_user(
            email="loginuser@example.com",
            password=self.password,
        )

    def test_login_page_is_available(self):
        response = self.client.get(reverse("account_login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/login.html")

    def test_user_can_log_in_with_email_and_password(self):
        response = self.client.post(
            reverse("account_login"),
            {
                "login": self.user.email,
                "password": self.password,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            str(self.client.session["_auth_user_id"]),
            str(self.user.pk),
        )

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            reverse("account_login"),
            {
                "login": self.user.email,
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)


class PasswordResetTests(TestCase):
    def test_password_reset_page_is_available(self):
        response = self.client.get(reverse("account_reset_password"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/password_reset.html")


class SocialLoginTests(TestCase):
    def test_google_login_page_is_available(self):
        response = self.client.get(reverse("google_login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "socialaccount/login.html")

    def test_github_login_page_is_available(self):
        response = self.client.get(reverse("github_login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "socialaccount/login.html")
