#!/bin/bash

# Virtual Environment Rebuild Script
# This script completely rebuilds the virtual environment and installs all dependencies

set -e  # Exit on error

echo "🔧 Rebuilding Virtual Environment"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Remove old virtual environment
if [ -d ".venv" ]; then
    echo -e "${YELLOW}🗑️  Removing old virtual environment...${NC}"
    rm -rf .venv
    echo -e "${GREEN}✅ Old virtual environment removed${NC}"
else
    echo -e "${BLUE}ℹ️  No existing virtual environment found${NC}"
fi
echo ""

# Step 2: Create new virtual environment
echo -e "${BLUE}📦 Creating new virtual environment...${NC}"
python3 -m venv .venv
echo -e "${GREEN}✅ Virtual environment created${NC}"
echo ""

# Step 3: Activate virtual environment
echo -e "${BLUE}🔄 Activating virtual environment...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Step 4: Upgrade pip
echo -e "${BLUE}⬆️  Upgrading pip, setuptools, and wheel...${NC}"
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✅ Core tools upgraded${NC}"
echo ""

# Step 5: Install core Django packages
echo -e "${BLUE}📚 Installing core packages...${NC}"
pip install Django>=5.1.3
pip install python-decouple>=3.8
pip install djangorestframework>=3.14.0
echo -e "${GREEN}✅ Core packages installed${NC}"
echo ""

# Step 6: Install database packages
echo -e "${BLUE}🗄️  Installing database packages...${NC}"
pip install psycopg2-binary>=2.9.9
echo -e "${GREEN}✅ Database packages installed${NC}"
echo ""

# Step 7: Install production packages
echo -e "${BLUE}🚀 Installing production packages...${NC}"
pip install whitenoise>=6.6.0
pip install gunicorn>=21.2.0
echo -e "${GREEN}✅ Production packages installed${NC}"
echo ""

# Step 8: Install caching packages (optional)
echo -e "${BLUE}💾 Installing caching packages...${NC}"
pip install django-redis>=5.4.0 redis>=5.0.1 || echo -e "${YELLOW}⚠️  Caching packages skipped (optional)${NC}"
echo ""

# Step 9: Verify installation
echo -e "${BLUE}🔍 Verifying installation...${NC}"
echo ""

echo "Python version:"
python --version
echo ""

echo "Pip version:"
pip --version
echo ""

echo "Installed packages:"
pip list
echo ""

# Step 10: Test Django
echo -e "${BLUE}🧪 Testing Django...${NC}"
python -c "import django; print(f'Django {django.get_version()} is working!')"
echo ""

# Step 11: Test python-decouple
echo -e "${BLUE}🧪 Testing python-decouple...${NC}"
python -c "import decouple; print('python-decouple is working!')"
echo ""

# Step 12: Test Django settings
echo -e "${BLUE}🧪 Testing Django settings...${NC}"
export DJANGO_ENVIRONMENT=development
python manage.py check
echo ""

# Summary
echo -e "${GREEN}✅ Virtual environment rebuild complete!${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "  - Virtual environment: .venv/"
echo "  - Python: $(python --version 2>&1)"
echo "  - Django: $(python -c 'import django; print(django.get_version())' 2>&1)"
echo ""
echo -e "${BLUE}🚀 Next steps:${NC}"
echo "  1. Activate venv: source .venv/bin/activate"
echo "  2. Run migrations: python manage.py migrate"
echo "  3. Start server: ./start-dev.sh"
echo ""
echo -e "${GREEN}Happy coding! 🎮✨${NC}"
