"""
ASGI config for alumni_portal project.
"""
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_portal_config.settings')
application = get_asgi_application()
