"""CafeMS – WSGI Application"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cafems.settings.development")
application = get_wsgi_application()
