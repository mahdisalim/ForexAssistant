"""
ASGI config for Forex Analysis Assistant project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forex_assistant.settings')

application = get_asgi_application()
