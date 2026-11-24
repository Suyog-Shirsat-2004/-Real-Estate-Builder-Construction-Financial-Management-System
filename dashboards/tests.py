"""Tests for the seven role dashboards and their permissions."""

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import UserProfile

DASHBOARD_NAMES = {
    UserProfile.ROLE_BUILDER: "dashboards:dashboard_builder",
    UserProfile.ROLE_SITE_ENGINEER: "dashboards:dashboard_site_engineer",
    UserProfile.ROLE_SITE_SUPERVISOR: "dashboards:dashboard_site_supervisor",
    UserProfile.ROLE_CONTRACTOR: "dashboards:dashboard_contractor",
    UserProfile.ROLE_STORE_MANAGER: "dashboards:dashboard_store_manager",
    UserProfile.ROLE_ACCOUNTANT: "dashboards:dashboard_accountant",
    UserProfile.ROLE_LABOUR: "dashboards:dashboard_labour",
}

DASHBOARD_TITLES = {
    UserProfile.ROLE_BUILDER: "Builder / Admin Dashboard",
    UserProfile.ROLE_SITE_ENGINEER: "Site Engineer Dashboard",
    UserProfile.ROLE_SITE_SUPERVISOR: "Site Supervisor Dashboard",
    UserProfile.ROLE_CONTRACTOR: "Contractor Dashboard",
    UserProfile.ROLE_STORE_MANAGER: "Store Manager Dashboard",
    UserProfile.ROLE_ACCOUNTANT: "Accountant Dashboard",
    UserProfile.ROLE_LABOUR: "Labour / Worker Dashboard",
}


def make_user(role, label):
    user = User.objects.create_user(
        username=f"{label}@example.com",
        email=f"{label}@example.com",
        password="Str0ng!Pass#2026",
        first_name=UserProfile(role=role).get_role_display(),
    )
    profile = user.profile
    profile.full_name = user.first_name
    profile.role = role
    profile.save(update_fields=["full_name", "role"])
    return user


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DashboardPermissionTests(TestCase):
    def setUp(self):
        self.users = {role: make_user(role, role.lower()) for role in DASHBOARD_NAMES}

    def test_anonymous_users_are_redirected_to_login(self):
        for name in DASHBOARD_NAMES.values():
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_each_role_only_opens_its_own_dashboard(self):
        for role, own_name in DASHBOARD_NAMES.items():
            for other_role, other_name in DASHBOARD_NAMES.items():
                if role == other_role:
                    continue
                with self.subTest(role=role, blocked=other_role):
                    self.client.force_login(self.users[role])
                    response = self.client.get(reverse(other_name))
                    self.assertEqual(response.status_code, 302)
                    self.assertNotEqual(response.url, reverse(other_name))

    def test_every_dashboard_renders_for_its_role(self):
        for role, name in DASHBOARD_NAMES.items():
            with self.subTest(role=role):
                self.client.force_login(self.users[role])
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, DASHBOARD_TITLES[role])
                self.assertContains(response, UserProfile(role=role).get_role_display())

    def test_dashboard_home_redirects_to_role_dashboard(self):
        for role, name in DASHBOARD_NAMES.items():
            with self.subTest(role=role):
                self.client.force_login(self.users[role])
                response = self.client.get(reverse("dashboards:dashboard_home"))
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, reverse(name))

    def test_legacy_workspaces_respect_roles(self):
        # Builder / Admin can open both workspaces.
        self.client.force_login(self.users[UserProfile.ROLE_BUILDER])
        self.assertEqual(self.client.get(reverse("manager_dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("supervisor_dashboard")).status_code, 200)

        # Engineers and supervisors can open only the field workspace.
        for role in (UserProfile.ROLE_SITE_ENGINEER, UserProfile.ROLE_SITE_SUPERVISOR):
            with self.subTest(role=role):
                self.client.force_login(self.users[role])
                self.assertEqual(self.client.get(reverse("supervisor_dashboard")).status_code, 200)
                self.assertEqual(self.client.get(reverse("manager_dashboard")).status_code, 302)

        # Remaining roles cannot open either workspace.
        for role in (
            UserProfile.ROLE_CONTRACTOR,
            UserProfile.ROLE_STORE_MANAGER,
            UserProfile.ROLE_ACCOUNTANT,
            UserProfile.ROLE_LABOUR,
        ):
            with self.subTest(role=role):
                self.client.force_login(self.users[role])
                for name in ("manager_dashboard", "supervisor_dashboard"):
                    self.assertEqual(self.client.get(reverse(name)).status_code, 302)

    def test_module_pages_and_json_are_protected(self):
        self.client.force_login(self.users[UserProfile.ROLE_SITE_ENGINEER])
        self.assertEqual(self.client.get(reverse("supervisor_assigned_sites")).status_code, 200)
        self.assertEqual(self.client.get(reverse("manager_projects")).status_code, 302)
        self.assertEqual(self.client.get(reverse("supervisor_dashboard_detail", args=["overview"])).status_code, 200)
        self.assertEqual(self.client.get(reverse("manager_dashboard_detail", args=["overview"])).status_code, 302)

    def test_inactive_account_is_denied(self):
        user = self.users[UserProfile.ROLE_BUILDER]
        profile = user.profile
        profile.account_status = UserProfile.STATUS_INACTIVE
        profile.save(update_fields=["account_status"])
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("dashboards:dashboard_builder")).status_code, 302)

    def test_no_profile_user_is_denied(self):
        # Signal normally creates a profile; simulate a legacy user without one.
        from accounts.models import UserProfile as Profile

        Profile.objects.filter(user=self.users[UserProfile.ROLE_BUILDER]).delete()
        self.client.force_login(self.users[UserProfile.ROLE_BUILDER])
        self.assertEqual(self.client.get(reverse("dashboards:dashboard_builder")).status_code, 302)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class LoginToWorkspaceTests(TestCase):
    """End-to-end: real login opens the role dashboard, which opens its workspace."""

    def setUp(self):
        self.users = {
            role: make_user(role, f"login_{role.lower()}")
            for role in (
                UserProfile.ROLE_BUILDER,
                UserProfile.ROLE_SITE_ENGINEER,
                UserProfile.ROLE_SITE_SUPERVISOR,
            )
        }

    def log_in(self, role):
        user = self.users[role]
        return self.client.post(
            reverse("accounts:login"),
            {
                "email": user.email,
                "password": "Str0ng!Pass#2026",
                "role": role,
            },
        )

    def test_builder_login_opens_manager_workspace(self):
        response = self.log_in(UserProfile.ROLE_BUILDER)
        self.assertEqual(response.url, reverse("dashboards:dashboard_builder"))

        response = self.client.get(reverse("dashboards:dashboard_builder"))
        self.assertContains(response, reverse("manager_dashboard"))

        for name in ("manager_dashboard", "manager_projects", "manager_sites", "manager_finance"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_engineer_and_supervisor_login_open_field_workspace(self):
        for role in (UserProfile.ROLE_SITE_ENGINEER, UserProfile.ROLE_SITE_SUPERVISOR):
            with self.subTest(role=role):
                self.client.logout()
                response = self.log_in(role)
                self.assertEqual(response.url, reverse(DASHBOARD_NAMES[role]))

                response = self.client.get(response.url)
                self.assertContains(response, reverse("supervisor_dashboard"))

                for name in (
                    "supervisor_dashboard",
                    "supervisor_assigned_sites",
                    "supervisor_dpr",
                    "supervisor_quality_checklist",
                    "supervisor_safety_checklist",
                ):
                    with self.subTest(name=name):
                        self.assertEqual(self.client.get(reverse(name)).status_code, 200)

                self.assertEqual(self.client.get(reverse("manager_dashboard")).status_code, 302)

    def test_workspace_header_shows_logged_in_role_and_logout(self):
        for role, workspace in (
            (UserProfile.ROLE_BUILDER, "manager_dashboard"),
            (UserProfile.ROLE_SITE_ENGINEER, "supervisor_dashboard"),
            (UserProfile.ROLE_SITE_SUPERVISOR, "supervisor_dashboard"),
        ):
            with self.subTest(role=role):
                self.client.logout()
                self.log_in(role)
                response = self.client.get(reverse(workspace))
                self.assertContains(response, UserProfile(role=role).get_role_display())
                self.assertContains(response, reverse("accounts:logout"))
                self.assertContains(response, "Logout")
                self.assertContains(response, reverse(DASHBOARD_NAMES[role]))
