from django.test import TestCase
from django.urls import reverse

from . import models


class SmokeTests(TestCase):
    def test_home_page_opens_without_login(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Real Estate Builder")

    def test_module_dashboards_open_without_login(self):
        for name in ["manager_dashboard", "supervisor_dashboard"]:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_sample_project_is_created(self):
        project = models.Project.objects.create(name="Test Tower", code="TEST-001")
        self.assertEqual(str(project), "TEST-001 - Test Tower")
