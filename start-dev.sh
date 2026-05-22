#!/bin/bash

# Development Server Startup Script
# This script starts the Django development server with development settings

set -e  # Exit on error

echo "🚀 Starting Elifwol Development Server"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.development exists
if [ ! -f .env.development ]; then
    echo -e "${YELLOW}⚠️  Warning: .env.development not found!${NC}"
    echo "Creating from .env.example..."
    cp .env.example .env.development
    echo -e "${GREEN}✅ Created .env.development${NC}"
fi

# Load development environment variables
export $(grep -v '^#' .env.development | xargs)
export DJANGO_ENVIRONMENT=development

echo -e "${BLUE}📋 Environment: ${DJANGO_ENVIRONMENT}${NC}"
echo -e "${BLUE}🗄️  Database: SQLite (db.sqlite3)${NC}"
echo -e "${BLUE}📧 Email: Console backend${NC}"
echo ""

# Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo -e "${GREEN}✅ Created logs directory${NC}"
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Warning: Virtual environment not activated${NC}"
    echo "Attempting to activate .venv..."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}✅ Activated .venv${NC}"
    else
        echo -e "${YELLOW}⚠️  No .venv found. Please activate your virtual environment manually.${NC}"
    fi
fi

# Check if python-decouple is installed
if ! python -c "import decouple" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  python-decouple not installed. Installing...${NC}"
    pip install python-decouple
    echo -e "${GREEN}✅ Installed python-decouple${NC}"
fi

# Run migrations
echo ""
echo -e "${BLUE}🔄 Running database migrations...${NC}"
python manage.py migrate --noinput

# Build CSS
echo ""
echo -e "${BLUE}🎨 Building Tailwind CSS...${NC}"
npm run build
echo -e "${GREEN}✅ CSS built${NC}"
echo -e "${YELLOW}   Tip: run 'npm run dev' in a separate terminal to watch for CSS changes${NC}"

# Collect static files (optional in development)
# echo ""
# echo -e "${BLUE}📦 Collecting static files...${NC}"
# python manage.py collectstatic --noinput --clear

echo ""
echo -e "${GREEN}✅ Development server ready!${NC}"
echo ""
echo -e "${BLUE}🌐 Server will be available at:${NC}"
echo -e "   ${GREEN}http://127.0.0.1:8000${NC}"
echo -e "   ${GREEN}http://localhost:8000${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start the development server
python manage.py runserver 0.0.0.0:8000
