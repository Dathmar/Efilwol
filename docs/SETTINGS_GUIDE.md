# Django Settings & Environment Configuration Guide

## 📋 Overview

The project now uses a **split settings architecture** with environment-based configuration using `python-decouple` and `.env` files.

### Benefits
- ✅ Separate development and production settings
- ✅ Secure secret management with `.env` files
- ✅ Easy environment switching
- ✅ No hardcoded secrets in code
- ✅ Production-ready security defaults

## 📁 Settings Structure

```
Efilwol/
├── settings/
│   ├── __init__.py          # Auto-imports correct settings
│   ├── base.py              # Common settings for all environments
│   ├── development.py       # Development-specific settings
│   └── production.py        # Production-specific settings
├── .env.development         # Development environment variables
├── .env.production          # Production environment variables (template)
├── .env.example             # Example environment file
├── start-dev.sh             # Start development server
├── start-prod.sh            # Start production server (Django runserver)
└── start-prod-gunicorn.sh   # Start production server (Gunicorn)
```

## 🚀 Quick Start

### Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start development server
./start-dev.sh

# Or manually:
export DJANGO_ENVIRONMENT=development
python manage.py runserver
```

### Production

```bash
# 1. Configure production environment
cp .env.example .env.production
# Edit .env.production with your production values

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start production server
./start-prod-gunicorn.sh

# Or manually:
export DJANGO_ENVIRONMENT=production
gunicorn Efilwol.wsgi:application --bind 0.0.0.0:8000
```

## 🔧 Environment Files

### `.env.development`
Used for local development. Contains safe defaults.

**Location:** Project root  
**Committed to git:** Yes (safe defaults)  
**Usage:** Automatically loaded by `start-dev.sh`

### `.env.production`
Used for production deployment. Contains sensitive data.

**Location:** Project root  
**Committed to git:** Yes (as template, update before use)  
**Usage:** Automatically loaded by `start-prod.sh`

### `.env.example`
Template file showing all available environment variables.

**Location:** Project root  
**Committed to git:** Yes  
**Usage:** Copy to create new environment files

## 📝 Environment Variables

### Core Django Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DJANGO_ENVIRONMENT` | Environment name | `development` | No |
| `SECRET_KEY` | Django secret key | Auto-generated | **Yes** |
| `DEBUG` | Debug mode | `False` | No |
| `ALLOWED_HOSTS` | Allowed hostnames | `localhost,127.0.0.1` | **Yes** |

### Database Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_ENGINE` | Database engine | `sqlite3` | No |
| `DB_NAME` | Database name | `db.sqlite3` | No |
| `DB_USER` | Database user | - | For PostgreSQL |
| `DB_PASSWORD` | Database password | - | For PostgreSQL |
| `DB_HOST` | Database host | - | For PostgreSQL |
| `DB_PORT` | Database port | `5432` | For PostgreSQL |

### URL Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BASE_URL` | Base URL | `http://127.0.0.1:8000` | No |
| `STATIC_URL` | Static files URL | `/static/` | No |
| `MEDIA_URL` | Media files URL | `/media/` | No |

### Email Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `EMAIL_BACKEND` | Email backend | `console` | No |
| `EMAIL_HOST` | SMTP host | - | For SMTP |
| `EMAIL_PORT` | SMTP port | `587` | For SMTP |
| `EMAIL_USE_TLS` | Use TLS | `True` | For SMTP |
| `EMAIL_HOST_USER` | SMTP username | - | For SMTP |
| `EMAIL_HOST_PASSWORD` | SMTP password | - | For SMTP |
| `DEFAULT_FROM_EMAIL` | From email | `noreply@elifwol.com` | No |

### Security Settings (Production)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECURE_SSL_REDIRECT` | Redirect to HTTPS | `True` | No |
| `SECURE_HSTS_SECONDS` | HSTS max age | `31536000` | No |
| `SESSION_COOKIE_SECURE` | Secure session cookie | `True` | No |
| `CSRF_COOKIE_SECURE` | Secure CSRF cookie | `True` | No |

### Cache Settings (Production)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CACHE_BACKEND` | Cache backend | `redis` | No |
| `REDIS_URL` | Redis URL | `redis://127.0.0.1:6379/1` | For Redis |

## 🔐 Security Best Practices

### 1. Generate a New Secret Key

**Never use the default secret key in production!**

```bash
# Generate a new secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Update `.env.production`:
```bash
SECRET_KEY=your-newly-generated-secret-key-here
```

### 2. Set DEBUG to False

In `.env.production`:
```bash
DEBUG=False
```

### 3. Configure ALLOWED_HOSTS

In `.env.production`:
```bash
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### 4. Use HTTPS in Production

In `.env.production`:
```bash
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 5. Use PostgreSQL in Production

In `.env.production`:
```bash
DB_ENGINE=django.db.backends.postgresql
DB_NAME=elifwol_production
DB_USER=elifwol_user
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432
```

## 🎯 Settings Files Explained

### `base.py`
Contains settings common to all environments:
- Installed apps
- Middleware
- Templates
- Password validators
- Internationalization
- Static files configuration
- Logging configuration

### `development.py`
Development-specific settings:
- `DEBUG = True`
- SQLite database
- Console email backend
- Permissive CORS
- Verbose logging
- No HTTPS requirements

### `production.py`
Production-specific settings:
- `DEBUG = False`
- PostgreSQL database
- SMTP email backend
- Redis caching
- WhiteNoise for static files
- Security headers
- HTTPS enforcement
- Error logging to file

## 🔄 Switching Environments

### Method 1: Environment Variable

```bash
# Development
export DJANGO_ENVIRONMENT=development
python manage.py runserver

# Production
export DJANGO_ENVIRONMENT=production
gunicorn Efilwol.wsgi:application
```

### Method 2: Shell Scripts

```bash
# Development
./start-dev.sh

# Production
./start-prod-gunicorn.sh
```

### Method 3: Django Settings Module

```bash
# Development
python manage.py runserver --settings=Efilwol.settings.development

# Production
gunicorn Efilwol.wsgi:application --env DJANGO_SETTINGS_MODULE=Efilwol.settings.production
```

## 📦 Dependencies

### Required for All Environments

```bash
pip install python-decouple
```

### Required for Production

```bash
pip install psycopg2-binary  # PostgreSQL
pip install whitenoise        # Static files
pip install gunicorn          # WSGI server
pip install django-redis      # Redis cache
pip install redis             # Redis client
```

### Install All

```bash
# Production
pip install -r requirements.txt

# Development (includes dev tools)
pip install -r requirements-dev.txt
```

## 🧪 Testing Configuration

### Test with Development Settings

```bash
export DJANGO_ENVIRONMENT=development
python manage.py test
```

### Test with Production Settings

```bash
export DJANGO_ENVIRONMENT=production
python manage.py check --deploy
```

## 🚀 Deployment Checklist

### Before Deploying to Production

- [ ] Generate new `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up PostgreSQL database
- [ ] Configure SMTP email
- [ ] Set up Redis cache
- [ ] Enable HTTPS settings
- [ ] Configure static files serving
- [ ] Set up logging directory
- [ ] Test with `python manage.py check --deploy`
- [ ] Run migrations
- [ ] Collect static files
- [ ] Create superuser

### Deployment Commands

```bash
# 1. Load production environment
export DJANGO_ENVIRONMENT=production

# 2. Run security check
python manage.py check --deploy

# 3. Run migrations
python manage.py migrate

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Create superuser (if needed)
python manage.py createsuperuser

# 6. Start server
gunicorn Efilwol.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

## 🐛 Troubleshooting

### Issue: "No module named 'decouple'"

**Solution:**
```bash
pip install python-decouple
```

### Issue: "ImproperlyConfigured: Set the SECRET_KEY"

**Solution:**
Create `.env.development` or `.env.production` with `SECRET_KEY` set.

### Issue: "ALLOWED_HOSTS must not be empty"

**Solution:**
Set `ALLOWED_HOSTS` in your `.env` file:
```bash
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Issue: Settings not loading

**Solution:**
Check `DJANGO_ENVIRONMENT` variable:
```bash
echo $DJANGO_ENVIRONMENT
```

### Issue: "No such file or directory: logs/django.log"

**Solution:**
Create logs directory:
```bash
mkdir -p logs
```

## 📚 Additional Resources

- [Django Settings Documentation](https://docs.djangoproject.com/en/5.1/topics/settings/)
- [python-decouple Documentation](https://github.com/HBNetwork/python-decouple)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

## 🔄 Migration from Old Settings

The old `Efilwol/settings.py` has been replaced with the new structure. If you need to rollback:

```bash
# Backup new settings
mv Efilwol/settings Efilwol/settings_new

# Restore old settings (if backed up)
git checkout HEAD~1 -- Efilwol/settings.py
```

## 💡 Tips

1. **Never commit `.env` with real secrets** - Use `.env.example` as template
2. **Use different databases** for dev and prod
3. **Test production settings locally** before deploying
4. **Monitor logs** in production
5. **Use environment variables** for all secrets
6. **Keep `.env.development`** in git for team consistency
7. **Document custom settings** in this file

---

**Need help?** Check the troubleshooting section or review the Django documentation.
