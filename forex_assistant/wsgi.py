"""
WSGI config for Forex Analysis Assistant project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forex_assistant.settings')

application = get_wsgi_application()
