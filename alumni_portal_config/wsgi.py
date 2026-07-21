"""
WSGI config for alumni_portal project.
"""
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_portal_config.settings')
application = get_wsgi_application()
