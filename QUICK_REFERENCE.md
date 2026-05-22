# 🚀 Quick Reference Card

## Essential Commands

### Setup (First Time)
```bash
./setup.sh                    # Complete project setup
```

### Development
```bash
./start-dev.sh                # Start dev server
npm run dev                   # Watch CSS changes
python manage.py migrate      # Run migrations
python manage.py createsuperuser  # Create admin user
```

### Production
```bash
./start-prod-gunicorn.sh      # Start prod server
python manage.py collectstatic  # Collect static files
python manage.py check --deploy  # Security check
```

## File Locations

### Configuration
- `.env.development` - Dev environment variables
- `.env.production` - Prod environment variables
- `Efilwol/settings/` - Django settings

### Frontend
- `base/templates/base/` - Base templates
- `game/templates/game/` - Game templates
- `game/static/js/` - Game JavaScript
- `tailwind.config.js` - Tailwind configuration

### Documentation
- `README.md` - Project overview
- `START_HERE.md` - Quick start
- `SETTINGS_GUIDE.md` - Settings docs

## Environment Variables

### Required
```bash
SECRET_KEY=your-secret-key
DEBUG=True/False
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Database
```bash
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

### URLs
```bash
BASE_URL=http://127.0.0.1:8000
```

## URLs

### Development
- Game: http://localhost:8000
- Admin: http://localhost:8000/admin

### API Endpoints
- Attack: `/api/v1/game/attack/{source}/{target}/{attack}/{type}/`

## Common Tasks

### Create Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Run Tests
```bash
python manage.py test
```

### Collect Static Files
```bash
python manage.py collectstatic
```

### Build CSS
```bash
npm run build
```

## Troubleshooting

### CSS not loading?
```bash
# Hard refresh
Ctrl+Shift+R
```

### Module not found?
```bash
pip install -r requirements.txt
```

### Database error?
```bash
python manage.py migrate
```

### Settings error?
```bash
# Check environment
echo $DJANGO_ENVIRONMENT
```

## Security Checklist

### Production
- [ ] New SECRET_KEY
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS set
- [ ] PostgreSQL configured
- [ ] HTTPS enabled
- [ ] Secure cookies enabled

## Documentation

| File | Purpose |
|------|---------|
| README.md | Project overview |
| START_HERE.md | Quick start |
| SETTINGS_GUIDE.md | Settings docs |
| FRONTEND_SETUP.md | Frontend guide |
| MIGRATION_GUIDE.md | Migration info |

## Tech Stack

- **Backend:** Django 5.1
- **Frontend:** Tailwind CSS + Alpine.js
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Server:** Gunicorn
- **Cache:** Redis (prod)

## Support

- 📚 Check documentation files
- 🐛 Check browser console
- 📝 Check Django logs
- 🔍 Review SETTINGS_GUIDE.md

---

**Quick Start:** `./setup.sh` → `./start-dev.sh` → http://localhost:8000
