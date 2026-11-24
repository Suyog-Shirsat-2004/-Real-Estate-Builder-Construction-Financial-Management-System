import re
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

from . import models


class SmokeTests(TestCase):
    def test_home_page_opens_without_login(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Real Estate Builder")

    def test_module_dashboards_require_login(self):
        for name in ["manager_dashboard", "supervisor_dashboard"]:
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_sample_project_is_created(self):
        project = models.Project.objects.create(name="Test Tower", code="TEST-001")
        self.assertEqual(str(project), "TEST-001 - Test Tower")


class PublicSiteTests(TestCase):
    def test_home_has_full_professional_layout(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        for section in ["id=\"home\"", "id=\"services\"", "id=\"features\"", "id=\"roles\"", "id=\"contact\""]:
            self.assertContains(response, section)
        for label in ["About Us", "Services", "Features", "Contact Us", "Project Management", "Financial Management", "Reports &amp; Analytics"]:
            self.assertContains(response, label)

    def test_home_hero_has_brand_and_role_logos_without_cta_buttons(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "real-estate-builder-logo.svg")
        self.assertContains(response, "Built for every role")
        self.assertNotContains(response, "Get Started Free")
        self.assertNotContains(response, "Login to Dashboard")
        login_url = reverse("accounts:login")
        for role in (
            "Builder / Admin", "Site Engineer", "Site Supervisor", "Contractor",
            "Store Manager", "Accountant", "Labour / Worker",
        ):
            with self.subTest(role=role):
                self.assertContains(response, f'href="{login_url}" title="{role}"')

    def test_home_role_cards_use_the_same_logos_as_login(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        for logo in (
            "builder-admin-logo.svg", "site-engineer-logo.svg", "site-supervisor-logo.svg",
            "contractor-logo.svg", "store-manager-logo.svg", "accountant-logo.svg",
            "labour-worker-logo.svg",
        ):
            with self.subTest(logo=logo):
                self.assertContains(response, f"images/{logo}")
        self.assertEqual(response.content.decode().count('class="reb-role-logo"'), 7)

    def test_seven_workspace_role_cards_link_to_login(self):
        response = self.client.get(reverse("home"))
        login_url = reverse("accounts:login")
        self.assertEqual(
            response.content.decode().count(f'class="reb-role-card" href="{login_url}"'),
            7,
        )
        self.assertNotContains(
            response,
            f'class="reb-role-card" href="{reverse("accounts:register")}"',
        )

    def test_home_nav_links_to_auth_pages(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("accounts:login"))
        self.assertContains(response, reverse("accounts:register"))

    def test_home_loads_animation_libraries(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "aos@2.3.4")
        self.assertContains(response, "animate.css/4.1.1")

    def test_home_feature_image_uses_existing_file(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "/static/images/site-manager-2.webp")

    def test_about_page_still_opens(self):
        self.assertEqual(self.client.get(reverse("about")).status_code, 200)

    def test_footer_has_centered_copyright_without_extra_blocks(self):
        response = self.client.get(reverse("home"))
        html = response.content.decode()
        self.assertContains(response, "&copy; 2026 Real Estate Builder. All rights reserved.")
        self.assertNotContains(response, "Built with Django")
        self.assertNotContains(response, "Get Started</h6>")
        self.assertNotContains(response, "Create your role-based account")
        self.assertNotContains(response, "Register Now")
        self.assertIn(
            '<div class="text-center small text-white-50">\n        <span>&copy; 2026 Real Estate Builder. All rights reserved.</span>',
            html,
        )

    def test_contact_details_are_updated_on_home_about_and_footer(self):
        for url in (reverse("home"), reverse("about")):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "Builder123@gmail.com")
                self.assertContains(response, "9977654735")
                self.assertContains(response, "Nashik, Maharashtra, India")
                self.assertContains(response, "mailto:Builder123@gmail.com")
                self.assertContains(response, "tel:9977654735")


class StaticFilesTests(TestCase):
    def test_every_template_static_reference_exists(self):
        template_dir = Path(settings.BASE_DIR) / "ConstructionManagement" / "templates"
        pattern = re.compile(r"\{%\s*static\s+'([^']+)'\s*%\}")
        refs = set()
        for path in template_dir.rglob("*.html"):
            refs.update(pattern.findall(path.read_text(encoding="utf-8")))
        self.assertTrue(refs)
        for ref in sorted(refs):
            with self.subTest(ref=ref):
                self.assertIsNotNone(finders.find(ref), f"Missing static file: {ref}")
