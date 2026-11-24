# Real Estate Builder — Construction & Financial Management System

A clean Django 6 + Bootstrap 5 application for managing construction projects from both a **Site Manager** and a **Site Supervisor** perspective.

## Quick start

```powershell
cd E:\Builder_01\Real_Estate_Builder_CFMS\RealEstateBuilder
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The home page opens directly — no login, registration, or redirect is required.

To reset the demo database:

```powershell
Remove-Item db.sqlite3
python manage.py migrate
python manage.py seed_demo
```

## Main routes

| Page | URL |
| --- | --- |
| Home / module selector | `/` |
| About & contact | `/about/` |
| Site Manager dashboard | `/manager/` |
| Site Supervisor dashboard | `/supervisor/` |

Django admin is available at `/admin/` for future authentication/role setup.

## Modules

### Site Manager

Dashboard, Project Management, Site Management, Construction Activities, Contractor Management, Material Management, Labour Management, Budget & Expenses, Daily Progress Reports, Project Timeline, Quality & Safety, Reports, Notifications, Settings.

### Site Supervisor

Dashboard, My Assigned Sites, Daily Work Updates, Labour Attendance, Material Consumption, Material Receiving, Construction Photos, Daily Progress Report, Site Issues, Quality Checklist, Safety Checklist, Reports, Notifications, Settings.

Every list page supports search, status filtering where applicable, detail view, create/edit forms, delete confirmation, status badges, progress bars, and responsive tables. Records are backed by SQLite through Django models and ModelForms.

## Project structure

```text
RealEstateBuilder/
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3
├── media/
├── RealEstateConfig/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── ConstructionManagement/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── context_processors.py
    ├── forms.py
    ├── models.py
    ├── tests.py
    ├── urls.py
    ├── views.py
    ├── migrations/
    ├── management/commands/seed_demo.py
    ├── templatetags/
    ├── static/
    │   ├── css/style.css
    │   ├── js/script.js
    │   └── images/
    └── templates/ConstructionManagement/
        ├── base.html
        ├── base_manager.html
        ├── base_supervisor.html
        ├── home.html
        ├── about.html
        ├── partials/
        ├── generic/
        ├── site_manager/
        └── site_supervisor/
```

## Technology

- Python 3.14, Django 6.1
- SQLite3
- HTML5, CSS3, Bootstrap 5, Bootstrap Icons
- Vanilla JavaScript
- Chart.js (CDN)

The UI is responsive for desktop, tablet, and mobile. An offline-capable local copy of Bootstrap/Chart.js can be added later if CDN access is unavailable.

## Tests

```powershell
python manage.py check
python manage.py test ConstructionManagement
```
