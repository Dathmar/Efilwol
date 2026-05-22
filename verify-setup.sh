#!/bin/bash

# Verification Script for Elifwol Setup
# This script verifies that the virtual environment and packages are installed correctly

set -e

echo "🔍 Verifying Elifwol Setup"
echo "=========================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Virtual environment exists${NC}"

# Activate virtual environment
source .venv/bin/activate

# Check Python version
echo ""
echo -e "${BLUE}🐍 Python Version:${NC}"
python --version

# Check pip version
echo ""
echo -e "${BLUE}📦 Pip Version:${NC}"
pip --version

# Check installed packages
echo ""
echo -e "${BLUE}📚 Checking Required Packages:${NC}"

packages=(
    "django"
    "decouple"
    "rest_framework"
    "psycopg2"
    "whitenoise"
    "gunicorn"
)

for package in "${packages[@]}"; do
    if python -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✅ $package${NC}"
    else
        echo -e "${RED}❌ $package (not installed)${NC}"
    fi
done

# Check Django
echo ""
echo -e "${BLUE}🎯 Django Version:${NC}"
python -c "import django; print(f'Django {django.get_version()}')"

# Check if settings work
echo ""
echo -e "${BLUE}⚙️  Checking Django Settings:${NC}"
export DJANGO_ENVIRONMENT=development
if python manage.py check --quiet 2>/dev/null; then
    echo -e "${GREEN}✅ Django settings are valid${NC}"
else
    echo -e "${RED}❌ Django settings have issues${NC}"
    python manage.py check
fi

# Check database
echo ""
echo -e "${BLUE}🗄️  Checking Database:${NC}"
if [ -f "db.sqlite3" ]; then
    echo -e "${GREEN}✅ Database exists${NC}"
else
    echo -e "${BLUE}ℹ️  Database not created yet (run migrations)${NC}"
fi

# Check .env file
echo ""
echo -e "${BLUE}📝 Checking Environment Files:${NC}"
if [ -f ".env" ] || [ -f ".env.development" ]; then
    echo -e "${GREEN}✅ Environment file exists${NC}"
else
    echo -e "${BLUE}ℹ️  No .env file (will use defaults)${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}✅ Setup verification complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Run migrations: python manage.py migrate"
echo "  2. Start server: ./start-dev.sh"
echo "  3. Visit: http://localhost:8000"
