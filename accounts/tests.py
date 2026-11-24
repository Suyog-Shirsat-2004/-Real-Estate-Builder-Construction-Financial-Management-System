"""Tests for registration, login, role selection and logout."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse

from .models import UserProfile

VALID_REGISTRATION = {
    "full_name": "Aarav Sharma",
    "email": "aarav@example.com",
    "mobile": "9876543210",
    "password1": "Str0ng!Pass#2026",
    "password2": "Str0ng!Pass#2026",
    "role": UserProfile.ROLE_BUILDER,
    "address": "12 Main Road, Bengaluru",
    "gender": "MALE",
    "terms": "on",
}


class RegistrationTests(TestCase):
    def test_registration_page_opens(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create your account")

    def test_registration_password_fields_are_visible_while_typing(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'type="text" name="password1"')
        self.assertContains(response, 'type="text" name="password2"')
        self.assertContains(response, "Password (visible)")
        self.assertContains(response, "Confirm Password (visible)")

    def test_registration_stores_profile_and_hashed_password(self):
        response = self.client.post(reverse("accounts:register"), VALID_REGISTRATION)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:login"))

        user = User.objects.get(email="aarav@example.com")
        self.assertNotEqual(user.password, VALID_REGISTRATION["password1"])
        self.assertTrue(user.password.startswith("pbkdf2_") or user.password.startswith("argon2"))
        self.assertEqual(user.username, "aarav@example.com")
        profile = user.profile
        self.assertEqual(profile.full_name, "Aarav Sharma")
        self.assertEqual(profile.mobile, "9876543210")
        self.assertEqual(profile.role, UserProfile.ROLE_BUILDER)
        self.assertEqual(profile.account_status, UserProfile.STATUS_ACTIVE)
        self.assertIsNotNone(profile.date_registered)

    def test_duplicate_email_is_rejected(self):
        self.client.post(reverse("accounts:register"), VALID_REGISTRATION)
        payload = dict(VALID_REGISTRATION, full_name="Second User", email="AARAV@example.com")
        response = self.client.post(reverse("accounts:register"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertEqual(User.objects.filter(email__iexact="aarav@example.com").count(), 1)

    def test_password_mismatch_is_rejected(self):
        payload = dict(VALID_REGISTRATION, password2="DifferentPass#2026")
        response = self.client.post(reverse("accounts:register"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "do not match")
        self.assertFalse(User.objects.exists())

    def test_simple_password_is_allowed(self):
        # Strong-password rules were relaxed on request: a simple, matching
        # password (even one similar to the name) must register successfully.
        payload = dict(VALID_REGISTRATION, password1="12345678", password2="12345678")
        response = self.client.post(reverse("accounts:register"), payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:login"))
        user = User.objects.get(email="aarav@example.com")
        self.assertTrue(user.check_password("12345678"))
        self.assertNotEqual(user.password, "12345678")

    def test_unique_collision_during_save_shows_friendly_error(self):
        # A double-submit race can pass validation, then fail the DB UNIQUE
        # constraint. It must render a clear error, never a 500 error page.
        with patch("accounts.views.RegistrationForm.save", side_effect=IntegrityError("UNIQUE constraint failed")):
            response = self.client.post(reverse("accounts:register"), VALID_REGISTRATION)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already registered")
        self.assertFalse(User.objects.exists())

    def test_invalid_mobile_is_rejected(self):
        payload = dict(VALID_REGISTRATION, mobile="12345")
        response = self.client.post(reverse("accounts:register"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "valid 10-digit")
        self.assertFalse(User.objects.exists())

    def test_terms_are_required(self):
        payload = dict(VALID_REGISTRATION)
        payload.pop("terms")
        response = self.client.post(reverse("accounts:register"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())


class LoginTests(TestCase):
    def setUp(self):
        self.client.post(reverse("accounts:register"), VALID_REGISTRATION)
        self.user = User.objects.get(email="aarav@example.com")

    def test_login_page_lists_all_seven_roles(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        for code, label in UserProfile.ROLE_CHOICES:
            self.assertContains(response, f'value="{code}"')
            self.assertContains(response, label)

    def test_login_aside_shows_all_roles_without_duplicate_brand(self):
        response = self.client.get(reverse("accounts:login"))
        # One brand in the navbar only; the old duplicate brand card is gone.
        self.assertNotContains(response, "auth-brand-mark")
        self.assertContains(response, "bi-buildings-fill")
        self.assertContains(response, "aside-role-list")
        for code, label in UserProfile.ROLE_CHOICES:
            with self.subTest(role=label):
                self.assertContains(response, f"<span>{label}</span>")

    def test_login_aside_shows_brand_logo_instead_of_old_heading(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertContains(response, "real-estate-builder-logo.svg")
        self.assertContains(response, "Construction &amp; Financial Management System")
        self.assertNotContains(response, "Secure, role-based access")
        self.assertNotContains(response, "Sign in with your registered email")

    def test_login_page_has_prominent_create_account_button(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertContains(response, "New here?")
        self.assertContains(
            response,
            f'href="{reverse("accounts:register")}" class="btn auth-btn-outline w-100 py-2"',
        )
        self.assertNotContains(
            response,
            '<a class="auth-link" href="' + reverse("accounts:register") + '">Create an account',
        )

    def test_every_role_card_and_side_item_has_a_simple_logo(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        for logo in (
            "builder-admin-logo.svg", "site-engineer-logo.svg", "site-supervisor-logo.svg",
            "contractor-logo.svg", "store-manager-logo.svg", "accountant-logo.svg",
            "labour-worker-logo.svg",
        ):
            with self.subTest(logo=logo):
                self.assertContains(response, logo)

        html = response.content.decode()
        self.assertEqual(html.count('class="role-card"'), 7)
        self.assertEqual(html.count('class="aside-role-logo"'), 7)
        self.assertNotContains(response, "Field roles")
        self.assertNotContains(response, "Popular")
        self.assertNotContains(response, "Open the field workspace")

    def test_role_mismatch_error_uses_bootstrap_danger_styling(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"email": "aarav@example.com", "password": VALID_REGISTRATION["password1"], "role": UserProfile.ROLE_ACCOUNTANT},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The selected role does not match this account")
        self.assertContains(response, "alert alert-danger")
        self.assertContains(response, "bi-exclamation-triangle-fill")
        self.assertNotContains(response, "alert alert-error")

    def test_first_visit_notice_appears_once_per_session(self):
        # A brand-new visitor (fresh session) gets the notice exactly once.
        visitor = Client()
        first = visitor.get(reverse("accounts:login"))
        self.assertContains(first, "Welcome to Real Estate Builder Management System!")
        second = visitor.get(reverse("accounts:login"))
        self.assertNotContains(second, "Welcome to Real Estate Builder Management System!")

    def test_wrong_password_is_rejected(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"email": "aarav@example.com", "password": "WrongPass#2026", "role": UserProfile.ROLE_BUILDER},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid email address or password")
        self.assertFalse(self.client.session.get("_auth_user_id"))

    def test_wrong_role_is_rejected(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"email": "aarav@example.com", "password": VALID_REGISTRATION["password1"], "role": UserProfile.ROLE_ACCOUNTANT},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "selected role does not match")
        self.assertFalse(self.client.session.get("_auth_user_id"))

    def test_correct_credentials_log_in_and_redirect_by_role(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"email": "AARAV@example.com", "password": VALID_REGISTRATION["password1"], "role": UserProfile.ROLE_BUILDER},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboards:dashboard_builder"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)

    def test_inactive_account_cannot_log_in(self):
        profile = self.user.profile
        profile.account_status = UserProfile.STATUS_INACTIVE
        profile.save(update_fields=["account_status"])
        response = self.client.post(
            reverse("accounts:login"),
            {"email": "aarav@example.com", "password": VALID_REGISTRATION["password1"], "role": UserProfile.ROLE_BUILDER},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not active")
        self.assertFalse(self.client.session.get("_auth_user_id"))

    def test_logout_requires_post_terminates_session(self):
        self.client.force_login(self.user)
        get_response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(get_response.status_code, 302)
        self.assertTrue(self.client.session.get("_auth_user_id"))

        response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))
        self.assertFalse(self.client.session.get("_auth_user_id"))
