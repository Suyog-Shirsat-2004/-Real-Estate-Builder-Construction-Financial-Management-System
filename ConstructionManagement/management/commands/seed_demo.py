"""Seed the database with realistic demo data for both dashboards."""

import io
import random
from datetime import date, timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw

from ConstructionManagement import models


class Command(BaseCommand):
    help = "Populate the database with demo construction data."

    def handle(self, *args, **options):
        random.seed(42)
        today = timezone.localdate()
        self.stdout.write("Seeding demo data...")

        projects = []
        for i, (name, client, status) in enumerate([
            ("Skyline Residency", "Urban Housing Ltd", models.StatusChoices.ACTIVE),
            ("Riverfront Commercial Complex", "Nexus Developers", models.StatusChoices.ACTIVE),
            ("Green Valley Villas", "GreenLife Realty", models.StatusChoices.PLANNED),
            ("Metro Tech Park", "City Infra Group", models.StatusChoices.ACTIVE),
        ], start=1):
            project, _ = models.Project.objects.get_or_create(
                code=f"PRJ-{i:03d}",
                defaults={
                    "name": name, "client": client, "location": "Bengaluru, Karnataka",
                    "start_date": today - timedelta(days=120 + i * 10),
                    "end_date": today + timedelta(days=240 - i * 10),
                    "budget": 25000000 + i * 5000000,
                    "progress": 20 + i * 15, "status": status,
                    "priority": models.PriorityChoices.HIGH, "manager": "Rahul Mehta",
                    "description": "Complete construction and financial management demonstration project.",
                },
            )
            projects.append(project)

        sites = []
        site_names = ["Tower A", "Tower B", "Block 1", "Block 2", "Podium", "Basement", "Club House", "Landscape"]
        supervisors = ["A. Supervisor", "S. Kumar", "M. Yadav", "P. Singh"]
        for i, name in enumerate(site_names):
            site, _ = models.Site.objects.get_or_create(
                code=f"SITE-{i + 1:03d}",
                defaults={
                    "project": projects[i % len(projects)], "name": name,
                    "location": f"Sector {i + 1}, Bengaluru",
                    "area_sqft": 18000 + i * 2500,
                    "start_date": today - timedelta(days=90 + i * 5),
                    "expected_completion": today + timedelta(days=150 - i * 5),
                    "progress": random.randint(10, 90),
                    "status": random.choice([models.StatusChoices.ACTIVE, models.StatusChoices.ACTIVE, models.StatusChoices.COMPLETED, models.StatusChoices.DELAYED]),
                    "supervisor": supervisors[i % len(supervisors)],
                    "description": "Active construction site with daily progress tracking.",
                },
            )
            sites.append(site)

        contractors = []
        for i, (name, specialty) in enumerate([
            ("Shiva Constructions", "Civil Works"), ("Electra Power Solutions", "Electrical"),
            ("Aqua Flow Systems", "Plumbing"), ("Green Interiors", "Finishing"),
            ("SafeBuild Services", "Safety & Scaffolding"),
        ], start=1):
            contractor, _ = models.Contractor.objects.get_or_create(
                name=name,
                defaults={
                    "company": name, "contact_person": f"Contact {i}",
                    "phone": f"98765{43210 + i}", "email": f"contact{i}@example.com",
                    "specialty": specialty, "contract_value": 800000 + i * 175000,
                    "start_date": today - timedelta(days=100),
                    "end_date": today + timedelta(days=200),
                    "rating": random.randint(3, 5), "status": models.StatusChoices.ACTIVE,
                },
            )
            contractors.append(contractor)

        materials = []
        for i, (name, category, unit) in enumerate([
            ("Cement", "Building Material", "bags"), ("Steel Rebar", "Building Material", "kg"),
            ("Sand", "Building Material", "cum"), ("Aggregate", "Building Material", "cum"),
            ("Bricks", "Building Material", "pcs"), ("Electrical Wire", "Electrical", "mtr"),
            ("PVC Pipes", "Plumbing", "pcs"), ("Paint", "Finishing", "ltr"),
            ("Safety Helmets", "Safety", "pcs"), ("Tiles", "Finishing", "sqft"),
        ], start=1):
            material, _ = models.Material.objects.get_or_create(
                name=name,
                defaults={
                    "category": category, "unit": unit,
                    "quantity_in_stock": random.randint(5, 500),
                    "reorder_level": random.randint(50, 100),
                    "unit_cost": random.randint(20, 800),
                    "supplier": "Prime Suppliers Pvt Ltd",
                    "last_restocked": today - timedelta(days=random.randint(1, 20)),
                },
            )
            materials.append(material)

        activity_types = ["Foundation", "Structure", "Masonry", "Electrical", "Plumbing", "Finishing"]
        for i in range(24):
            models.Activity.objects.get_or_create(
                title=f"{random.choice(activity_types)} Work - Phase {i + 1}",
                site=sites[i % len(sites)],
                defaults={
                    "project": sites[i % len(sites)].project,
                    "contractor": contractors[i % len(contractors)],
                    "description": "Construction activity tracked by site manager and supervisor.",
                    "activity_type": activity_types[i % len(activity_types)],
                    "start_date": today - timedelta(days=random.randint(0, 20)),
                    "end_date": today + timedelta(days=random.randint(1, 30)),
                    "progress": random.randint(0, 100),
                    "status": random.choice(list(models.StatusChoices)),
                    "priority": random.choice(list(models.PriorityChoices)),
                    "assigned_to": supervisors[i % len(supervisors)],
                },
            )

        for i in range(6):
            models.MaterialRequest.objects.get_or_create(
                site=sites[i % len(sites)], material=materials[i], quantity=random.randint(10, 100),
                defaults={
                    "requested_by": supervisors[i % len(supervisors)],
                    "request_date": today - timedelta(days=i),
                    "needed_date": today + timedelta(days=3 - i),
                    "status": random.choice([models.StatusChoices.PLANNED, models.StatusChoices.ACTIVE]),
                    "remarks": "Required for ongoing site work.",
                },
            )

        for i in range(20):
            models.MaterialTransaction.objects.get_or_create(
                site=sites[i % len(sites)], material=materials[i % len(materials)],
                transaction_type="RECEIVED" if i % 2 == 0 else "CONSUMED",
                quantity=random.randint(5, 80), date=today - timedelta(days=i % 7),
                defaults={
                    "reference": f"MRN-{1000 + i}", "recorded_by": supervisors[i % len(supervisors)],
                    "notes": "Demo material movement record.",
                },
            )

        worker_names = ["Arjun Kumar", "Ravi Shankar", "Imran Shaikh", "Suresh Yadav", "Manjunath", "Deepak", "Sanaullah", "Vikram", "Rakesh", "Naveen"]
        workers = []
        for i in range(20):
            worker, _ = models.Labour.objects.get_or_create(
                worker_id=f"LAB-{i + 1:03d}",
                defaults={
                    "name": worker_names[i % len(worker_names)] + f" {i // len(worker_names) + 1}",
                    "role": random.choice(["Mason", "Electrician", "Plumber", "Helper", "Carpenter"]),
                    "site": sites[i % len(sites)], "phone": f"98{i:07d}",
                    "daily_wage": random.randint(500, 1200),
                    "join_date": today - timedelta(days=random.randint(30, 200)),
                    "status": models.StatusChoices.ACTIVE,
                },
            )
            workers.append(worker)

        for i, worker in enumerate(workers):
            models.Attendance.objects.get_or_create(
                labour=worker, date=today,
                defaults={
                    "site": worker.site,
                    "status": "ABSENT" if i % 7 == 0 else "PRESENT",
                    "check_in": "08:00", "check_out": "17:00",
                    "remarks": "Demo attendance record.",
                },
            )

        for project in projects:
            for category in ["Civil", "Electrical", "Plumbing", "Finishing"]:
                models.Budget.objects.get_or_create(
                    project=project, category=category, year=today.year,
                    defaults={
                        "allocated": random.randint(2000000, 6000000),
                        "spent": random.randint(500000, 4000000),
                        "month": 1,
                        "notes": "Monthly budget allocation.",
                    },
                )

        for i in range(24):
            models.Expense.objects.get_or_create(
                category=activity_types[i % len(activity_types)],
                description=f"Expense voucher {1000 + i}", amount=random.randint(10000, 250000),
                date=today - timedelta(days=i * 5),
                defaults={
                    "project": projects[i % len(projects)],
                    "vendor": "Vendor Solutions",
                    "status": random.choice([models.StatusChoices.COMPLETED, models.StatusChoices.PLANNED]),
                    "approved_by": "Rahul Mehta",
                },
            )

        for i in range(10):
            day = today - timedelta(days=i)
            for site in sites[:4]:
                models.DailyProgressReport.objects.get_or_create(
                    site=site, date=day,
                    defaults={
                        "project": site.project,
                        "summary": f"Progress update for {site.name}.",
                        "work_completed": "Foundation and structural work progressed as planned.",
                        "labour_count": random.randint(15, 45),
                        "material_used": "Cement 50 bags, Steel 800 kg",
                        "issues": "Minor material delay" if i % 3 == 0 else "None",
                        "weather": "Clear", "progress_percentage": min(100, site.progress + i),
                        "submitted_by": site.supervisor,
                        "status": models.StatusChoices.PLANNED if i % 2 == 0 else models.StatusChoices.COMPLETED,
                    },
                )

        for i, project in enumerate(projects):
            for j in range(3):
                models.ProjectMilestone.objects.get_or_create(
                    project=project, title=f"Milestone {j + 1} - {project.name}",
                    defaults={
                        "description": "Key project milestone.",
                        "due_date": today + timedelta(days=15 + j * 30 + i * 5),
                        "progress": random.randint(0, 80),
                        "status": random.choice([models.StatusChoices.PLANNED, models.StatusChoices.ACTIVE]),
                    },
                )

        for i in range(6):
            models.QualityInspection.objects.get_or_create(
                site=sites[i % len(sites)], inspection_date=today - timedelta(days=i), area=f"Area {i + 1}",
                defaults={
                    "project": sites[i % len(sites)].project, "inspector": "Quality Team",
                    "score": random.randint(60, 98), "status": models.StatusChoices.COMPLETED,
                    "findings": "Minor finishing observations.", "recommendations": "Rectify within 7 days.",
                },
            )
            models.SafetyInspection.objects.get_or_create(
                site=sites[i % len(sites)], inspection_date=today - timedelta(days=i), area=f"Zone {i + 1}",
                defaults={
                    "inspector": "Safety Officer", "score": random.randint(55, 95),
                    "status": random.choice([models.StatusChoices.ACTIVE, models.StatusChoices.DELAYED]),
                    "findings": "PPE compliance checked.", "recommendations": "Continue daily safety briefings.",
                },
            )

        for i, title in enumerate(["Water leakage in basement", "Steel delivery delayed", "Scaffold inspection pending", "Electrical conduit misalignment", "Labour shortage", "Material quality issue"]):
            models.SiteIssue.objects.get_or_create(
                title=title, site=sites[i % len(sites)],
                defaults={
                    "description": "Issue reported from site for management review.",
                    "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                    "status": models.StatusChoices.ACTIVE if i % 3 else models.StatusChoices.COMPLETED,
                    "reported_by": supervisors[i % len(supervisors)],
                    "reported_date": today - timedelta(days=i),
                    "resolution": "Pending" if i % 3 else "Resolved by site team.",
                },
            )

        colors = [(0, 123, 187), (45, 150, 90), (220, 160, 45), (110, 90, 180), (190, 80, 80), (60, 150, 170)]
        for i, site in enumerate(sites[:6]):
            photo, created = models.ConstructionPhoto.objects.get_or_create(
                title=f"Site Progress Photo {i + 1}", site=site,
                defaults={
                    "caption": "Daily construction progress photograph.",
                    "taken_at": today - timedelta(days=i), "uploaded_by": site.supervisor,
                },
            )
            if created:
                img = Image.new("RGB", (640, 360), colors[i % len(colors)])
                draw = ImageDraw.Draw(img)
                draw.rectangle([40, 40, 600, 320], outline=(255, 255, 255), width=4)
                draw.text((70, 170), f"{site.name} - Progress", fill=(255, 255, 255))
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                photo.image.save(f"site_progress_{i + 1}.png", ContentFile(buffer.getvalue()), save=False)
                photo.save()

        for i, (title, category, audience) in enumerate([
            ("Material delivery scheduled", "Material", "SUPERVISOR"),
            ("DPR verification pending", "DPR", "MANAGER"),
            ("Safety drill on Friday", "Safety", "ALL"),
            ("Budget review meeting", "Finance", "MANAGER"),
            ("Quality audit completed", "Quality", "ALL"),
            ("New labour joining", "Labour", "SUPERVISOR"),
        ]):
            models.Notification.objects.get_or_create(
                title=title,
                defaults={
                    "message": "This is a demo notification for the construction management system.",
                    "category": category, "audience": audience,
                    "is_read": i % 3 == 0, "link": "#",
                },
            )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
