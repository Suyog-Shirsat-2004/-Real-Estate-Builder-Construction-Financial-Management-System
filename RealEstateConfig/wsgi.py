"""WSGI config for RealEstateConfig project."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RealEstateConfig.settings")

application = get_wsgi_application()
