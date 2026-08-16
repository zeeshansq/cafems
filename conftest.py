"""
pytest configuration for CafeMS.
"""
import django
from django.conf import settings


def pytest_configure(config):
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cafems.settings.development")
    os.environ.setdefault("SECRET_KEY", "django-insecure-ci-testing-key-cafems-test-suite-2026")
