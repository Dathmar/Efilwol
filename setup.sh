#!/bin/bash

# Elifwol Setup Script
# This script sets up the project for first-time use

set -e  # Exit on error

echo "🎮 Elifwol Project Setup"
echo "========================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Python version
echo -e "${BLUE}🐍 Checking Python version...${NC}"
python_version=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python $python_version${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  No virtual environment found${NC}"
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python -m venv .venv
    echo -e "${GREEN}✅ Created .venv${NC}"
    echo ""
fi

# Activate virtual environment
echo -e "${BLUE}🔄 Activating virtual environment...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ Python dependencies installed${NC}"
echo ""

# Check Node.js
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo -e "${GREEN}✅ Node.js $node_version${NC}"
    
    # Install Node dependencies
    if [ -f "package.json" ]; then
        echo -e "${BLUE}📦 Installing Node dependencies...${NC}"
        npm install
        echo -e "${GREEN}✅ Node dependencies installed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Node.js not found (optional for frontend development)${NC}"
fi
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${BLUE}📝 Creating .env file...${NC}"
    cp .env.development .env
    echo -e "${GREEN}✅ Created .env from .env.development${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi
echo ""

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p logs
mkdir -p staticfiles
mkdir -p media
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Make scripts executable
echo -e "${BLUE}🔧 Making scripts executable...${NC}"
chmod +x start-dev.sh start-prod.sh start-prod-gunicorn.sh
echo -e "${GREEN}✅ Scripts are executable${NC}"
echo ""

# Run migrations
echo -e "${BLUE}🔄 Running database migrations...${NC}"
export DJANGO_ENVIRONMENT=development
python manage.py migrate
echo -e "${GREEN}✅ Migrations complete${NC}"
echo ""

# Create superuser prompt
echo -e "${YELLOW}Would you like to create a superuser? (y/n)${NC}"
read -r create_superuser
if [ "$create_superuser" = "y" ] || [ "$create_superuser" = "Y" ]; then
    python manage.py createsuperuser
fi
echo ""

# Summary
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${BLUE}📚 Next steps:${NC}"
echo ""
echo -e "  1. Start development server:"
echo -e "     ${GREEN}./start-dev.sh${NC}"
echo ""
echo -e "  2. Visit your game:"
echo -e "     ${GREEN}http://localhost:8000${NC}"
echo ""
echo -e "  3. Read the documentation:"
echo -e "     ${GREEN}START_HERE.md${NC} - Quick start"
echo -e "     ${GREEN}SETTINGS_GUIDE.md${NC} - Settings configuration"
echo -e "     ${GREEN}FRONTEND_SETUP.md${NC} - Frontend development"
echo ""
echo -e "${YELLOW}Happy coding! 🎮✨${NC}"
