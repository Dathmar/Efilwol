"""
Django settings module selector.

Automatically imports the correct settings based on DJANGO_SETTINGS_MODULE
environment variable or defaults to development settings.
"""

import os

# Default to development settings if not specified
ENVIRONMENT = os.getenv('DJANGO_ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    from .production import *
else:
    from .development import *
