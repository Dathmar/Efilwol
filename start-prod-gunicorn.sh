#!/bin/bash

# Production Server Startup Script with Gunicorn
# This script starts the Django application using Gunicorn (recommended for production)

set -e  # Exit on error

echo "🚀 Starting Elifwol Production Server (Gunicorn)"
echo "================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo -e "${RED}❌ Error: .env.production not found!${NC}"
    exit 1
fi

# Load production environment variables
export $(grep -v '^#' .env.production | xargs)
export DJANGO_ENVIRONMENT=production

# Security checks
if [ "$DEBUG" = "True" ]; then
    echo -e "${RED}❌ ERROR: DEBUG is True in production!${NC}"
    exit 1
fi

# Create necessary directories
mkdir -p logs staticfiles media

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo -e "${RED}❌ No virtual environment found${NC}"
        exit 1
    fi
fi

# Install/check Gunicorn
if ! python -c "import gunicorn" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Gunicorn not installed. Installing...${NC}"
    pip install gunicorn
fi

# Run migrations
echo -e "${BLUE}🔄 Running migrations...${NC}"
python manage.py migrate --noinput

# Collect static files
echo -e "${BLUE}📦 Collecting static files...${NC}"
python manage.py collectstatic --noinput --clear

echo ""
echo -e "${GREEN}✅ Starting Gunicorn server...${NC}"
echo ""

# Gunicorn configuration
WORKERS=${GUNICORN_WORKERS:-4}
TIMEOUT=${GUNICORN_TIMEOUT:-120}
BIND=${GUNICORN_BIND:-0.0.0.0:8000}
LOG_LEVEL=${GUNICORN_LOG_LEVEL:-info}

# Start Gunicorn
exec gunicorn Efilwol.wsgi:application \
    --bind $BIND \
    --workers $WORKERS \
    --timeout $TIMEOUT \
    --log-level $LOG_LEVEL \
    --access-logfile logs/gunicorn-access.log \
    --error-logfile logs/gunicorn-error.log \
    --capture-output \
    --enable-stdio-inheritance
