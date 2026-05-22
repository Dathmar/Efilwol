"""
Development settings for Efilwol project.

These settings are optimized for local development.
"""

from .base import *

# Debug mode enabled for development
DEBUG = True

# Allowed hosts for development
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '[::1]']

# Database - SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email backend - console for development (prints to terminal)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files - no need for whitenoise in development
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Development-specific middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Disable HTTPS redirects in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS settings for development (if needed)
CORS_ALLOW_ALL_ORIGINS = True

# Logging - more verbose in development
LOGGING['loggers']['django']['level'] = 'DEBUG'

# Django Debug Toolbar (optional - uncomment if installed)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
# INTERNAL_IPS = ['127.0.0.1']

# Development-specific settings
TEMPLATES[0]['OPTIONS']['debug'] = True

# Cache - dummy cache for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Base URL for development
BASE_URL = 'http://127.0.0.1:8000'

print("🚀 Running in DEVELOPMENT mode")
print(f"📁 BASE_DIR: {BASE_DIR}")
print(f"🗄️  Database: SQLite (db.sqlite3)")
print(f"📧 Email: Console backend")
print(f"🔗 BASE_URL: {BASE_URL}")
