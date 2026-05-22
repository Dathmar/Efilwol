#!/bin/bash
source .venv/bin/activate
export DJANGO_ENVIRONMENT=development
python manage.py test game api script users --verbosity=2
