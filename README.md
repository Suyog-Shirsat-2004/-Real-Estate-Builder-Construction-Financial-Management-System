# Real Estate Builder — Construction & Financial Management System

A Django-based Real Estate Builder Construction and Financial Management System to manage construction projects, site operations, employees, contractors, materials, inventory, expenses, payments, and financial reports.

A clean Django 6 + Bootstrap 5 application with a professional public website, secure registration/login, and **seven role-based dashboards** for the whole project team.

## Quick start

```powershell
cd E:\Builder_01\Real_Estate_Builder_CFMS\RealEstateBuilder
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The public home page opens without login. Click **Register** to create an account, then **Login** with your registered email, password and role to open your dashboard. No hardcoded or demo credentials are provided.

Password-reset emails are printed in the terminal during development (console email backend).

To recreate a fresh demo database from scratch (this deletes accounts and seeded records):

```powershell
Remove-Item db.sqlite3
python manage.py migrate
python manage.py seed_demo
```

## Main routes

| Page | URL | Access |
| --- | --- | --- |
| Public home (hero, services, features, roles, gallery, contact) | `/` | Public |
| About & contact | `/about/` | Public |
| Register | `/accounts/register/` | Public |
| Login / Forgot password | `/accounts/login/` / `/accounts/password-reset/` | Public |
| Dashboard router | `/dashboard/` | Logged in |
| Builder / Admin | `/dashboard/builder/` | Builder only |
| Site Engineer | `/dashboard/site-engineer/` | Site Engineer only |
| Site Supervisor | `/dashboard/site-supervisor/` | Site Supervisor only |
| Contractor | `/dashboard/contractor/` | Contractor only |
| Store Manager | `/dashboard/store-manager/` | Store Manager only |
| Accountant | `/dashboard/accountant/` | Accountant only |
| Labour / Worker | `/dashboard/labour/` | Labour only |
| Manager workspace | `/manager/` | Builder only |
| Field workspace | `/supervisor/` | Builder, Site Engineer, Site Supervisor |

Direct URLs to any protected page redirect to login; wrong roles are denied. Django admin is available at `/admin/`.

## Modules

### Site Manager

Dashboard, Project Management, Site Management, Construction Activities, Contractor Management, Material Management, Labour Management, Budget & Expenses, Daily Progress Reports, Project Timeline, Quality & Safety, Reports, Notifications, Settings.

### Site Supervisor

Dashboard, My Assigned Sites, Daily Work Updates, Labour Attendance, Material Consumption, Material Receiving, Construction Photos, Daily Progress Report, Site Issues, Quality Checklist, Safety Checklist, Reports, Notifications, Settings.

Every list page supports search, status filtering where applicable, detail view, create/edit forms, delete confirmation, status badges, progress bars, and responsive tables. Records are backed by SQLite through Django models and ModelForms.

## Accounts, roles and permissions

- Registration stores full name, unique email, validated 10-digit mobile, hashed password, role, address, optional gender and profile photo, terms acceptance, registration date and last login.
- Login requires the registered **email + password + matching role**. A wrong role, wrong password, inactive account, or missing profile is rejected. A first-visit notice is shown once per session.
- Each successful login redirects to the matching dashboard: Builder, Site Engineer, Site Supervisor, Contractor, Store Manager, Accountant or Labour / Worker.
- `accounts/` owns the user profile, forms, views and role decorators. `dashboards/` owns the seven protected role views and templates.
- The existing Manager workspace is Builder-only; the Field workspace is available to Builder, Site Engineer and Site Supervisor.
- Once logged in, the role dashboard links to the matching workspace (`site_manager/` or `site_supervisor/` templates). The workspace header shows the signed-in role, links back to that role's dashboard, and includes a secure POST logout button.

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
├── accounts/
│   ├── models.py          # UserProfile (role, status, profile data)
│   ├── forms.py           # Registration and login forms with validation
│   ├── views.py           # Register, login, logout
│   ├── decorators.py      # role_required / module_access_required
│   ├── urls.py            # /accounts/... routes
│   ├── signals.py         # creates a profile for every Django user
│   ├── tests.py
│   └── templates/accounts/, templates/registration/
├── dashboards/
│   ├── views.py           # seven role dashboards
│   ├── urls.py            # /dashboard/... routes
│   ├── tests.py
│   └── templates/dashboards/
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
- Chart.js (CDN), AOS scroll animations, Animate.css, Google Fonts (Poppins)

The UI is responsive for desktop, tablet, and mobile. An offline-capable local copy of Bootstrap/Chart.js can be added later if CDN access is unavailable.

## Tests

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test accounts dashboards ConstructionManagement
```
