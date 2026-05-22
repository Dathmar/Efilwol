#!/bin/bash

# Production Server Startup Script
# This script prepares and starts the Django application in production mode
# Note: This uses Django's runserver for demonstration. Use Gunicorn/uWSGI in real production!

set -e  # Exit on error

echo "🚀 Starting Elifwol Production Server"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo -e "${RED}❌ Error: .env.production not found!${NC}"
    echo "Please create .env.production with your production settings."
    echo "You can copy .env.example and modify it:"
    echo "  cp .env.example .env.production"
    exit 1
fi

# Load production environment variables
export $(grep -v '^#' .env.production | xargs)
export DJANGO_ENVIRONMENT=production

echo -e "${BLUE}📋 Environment: ${DJANGO_ENVIRONMENT}${NC}"
echo -e "${BLUE}🗄️  Database: ${DB_ENGINE}${NC}"
echo -e "${BLUE}📧 Email: SMTP backend${NC}"
echo ""

# Security checks
if [ "$DEBUG" = "True" ]; then
    echo -e "${RED}❌ ERROR: DEBUG is True in production!${NC}"
    echo "Set DEBUG=False in .env.production"
    exit 1
fi

if [ "$SECRET_KEY" = "CHANGE-THIS-TO-A-SECURE-RANDOM-SECRET-KEY-IN-PRODUCTION" ]; then
    echo -e "${RED}❌ ERROR: SECRET_KEY not changed!${NC}"
    echo "Generate a new secret key and update .env.production"
    echo "Run: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
    exit 1
fi

if [ "$ALLOWED_HOSTS" = "yourdomain.com,www.yourdomain.com" ]; then
    echo -e "${YELLOW}⚠️  Warning: ALLOWED_HOSTS still has default value${NC}"
    echo "Update ALLOWED_HOSTS in .env.production with your actual domain"
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p logs
mkdir -p staticfiles
mkdir -p media
echo -e "${GREEN}✅ Directories created${NC}"

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Warning: Virtual environment not activated${NC}"
    echo "Attempting to activate .venv..."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}✅ Activated .venv${NC}"
    else
        echo -e "${RED}❌ No .venv found. Please activate your virtual environment.${NC}"
        exit 1
    fi
fi

# Check if required packages are installed
echo ""
echo -e "${BLUE}📦 Checking dependencies...${NC}"
if ! python -c "import decouple" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  python-decouple not installed. Installing...${NC}"
    pip install python-decouple
fi

if ! python -c "import psycopg2" 2>/dev/null && [ "$DB_ENGINE" = "django.db.backends.postgresql" ]; then
    echo -e "${YELLOW}⚠️  psycopg2 not installed. Installing...${NC}"
    pip install psycopg2-binary
fi

if ! python -c "import whitenoise" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  whitenoise not installed. Installing...${NC}"
    pip install whitenoise
fi

echo -e "${GREEN}✅ Dependencies checked${NC}"

# Run migrations
echo ""
echo -e "${BLUE}🔄 Running database migrations...${NC}"
python manage.py migrate --noinput

# Collect static files
echo ""
echo -e "${BLUE}📦 Collecting static files...${NC}"
python manage.py collectstatic --noinput --clear

# Create superuser if needed (optional)
# echo ""
# echo -e "${BLUE}👤 Creating superuser...${NC}"
# python manage.py createsuperuser --noinput || true

echo ""
echo -e "${GREEN}✅ Production server ready!${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: This script uses Django's runserver for demonstration.${NC}"
echo -e "${YELLOW}   For real production, use Gunicorn, uWSGI, or similar WSGI server.${NC}"
echo ""
echo -e "${BLUE}🌐 Server will be available at:${NC}"
echo -e "   ${GREEN}${BASE_URL}${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start the server
# For production, replace this with Gunicorn:
# gunicorn Efilwol.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120

python manage.py runserver 0.0.0.0:8000
