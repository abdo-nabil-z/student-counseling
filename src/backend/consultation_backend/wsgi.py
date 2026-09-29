"""
WSGI config for consultation_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import logging
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'consultation_backend.settings')

application = get_wsgi_application()

# Seed blank templates with their defaults once, now that Django (and its DB
# connection) is ready, before the app starts serving requests.
from django.db.utils import DatabaseError  # noqa: E402
from templates.defaults import seed_empty_templates  # noqa: E402

try:
    seed_empty_templates()
except DatabaseError:
    logging.getLogger(__name__).warning(
        "Skipped seeding default templates — database not ready (migrations pending?)."
    )
