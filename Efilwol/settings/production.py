"""
Production settings for Efilwol project.

These settings are optimized for production deployment.
Security-focused with performance optimizations.
"""

from .base import *

# Debug mode MUST be False in production
DEBUG = False

# Allowed hosts - must be set via environment variable
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Security settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Session security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# CSRF security
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Database - should be PostgreSQL in production
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Static files - use WhiteNoise for serving static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Email backend - real SMTP in production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Cache - Redis recommended for production
CACHES = {
    'default': {
        'BACKEND': config(
            'CACHE_BACKEND',
            default='django.core.cache.backends.redis.RedisCache'
        ),
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'KEY_PREFIX': 'elifwol',
        'TIMEOUT': 300,
    }
}

# Session backend - use cache for better performance
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Logging - production logging to file
LOGGING['handlers']['file']['filename'] = config(
    'LOG_FILE_PATH',
    default=str(BASE_DIR / 'logs' / 'production.log')
)
LOGGING['loggers']['django']['level'] = config('DJANGO_LOG_LEVEL', default='WARNING')

# Add error logging
LOGGING['handlers']['error_file'] = {
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': BASE_DIR / 'logs' / 'errors.log',
    'maxBytes': 1024 * 1024 * 10,  # 10 MB
    'backupCount': 5,
    'formatter': 'app',
    'level': 'ERROR',
}
LOGGING['loggers']['django']['handlers'].append('error_file')

# Admin email for error notifications
ADMINS = [
    (config('ADMIN_NAME', default='Admin'), config('ADMIN_EMAIL', default='admin@elifwol.com')),
]
MANAGERS = ADMINS

# Base URL for production
BASE_URL = config('BASE_URL')

# CORS settings (if using separate frontend)
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='', cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# Content Security Policy (optional but recommended)
# CSP_DEFAULT_SRC = ("'self'",)
# CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://unpkg.com")
# CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
# CSP_IMG_SRC = ("'self'", "data:", "https:")
# CSP_FONT_SRC = ("'self'", "https://cdn.jsdelivr.net")

print("🚀 Running in PRODUCTION mode")
print(f"📁 BASE_DIR: {BASE_DIR}")
print(f"🗄️  Database: {DATABASES['default']['ENGINE']}")
print(f"📧 Email: SMTP backend")
print(f"🔗 BASE_URL: {BASE_URL}")
print(f"🔒 Security: SSL redirect enabled, HSTS enabled")
