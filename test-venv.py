#!/usr/bin/env python
"""Test script to verify virtual environment setup"""

import sys
import os

print("=" * 50)
print("Virtual Environment Test")
print("=" * 50)
print()

# Check Python version
print(f"Python Version: {sys.version}")
print(f"Python Executable: {sys.executable}")
print()

# Check if we're in a virtual environment
in_venv = hasattr(sys, 'real_prefix') or (
    hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
)
print(f"In Virtual Environment: {in_venv}")
print()

# Try importing required packages
packages = {
    'django': 'Django',
    'decouple': 'python-decouple',
    'rest_framework': 'djangorestframework',
    'psycopg2': 'psycopg2-binary',
    'whitenoise': 'whitenoise',
    'gunicorn': 'gunicorn',
}

print("Package Status:")
print("-" * 50)

installed = []
missing = []

for module, package in packages.items():
    try:
        __import__(module)
        print(f"✅ {package}")
        installed.append(package)
    except ImportError:
        print(f"❌ {package} (not installed)")
        missing.append(package)

print()
print(f"Installed: {len(installed)}/{len(packages)}")

if missing:
    print()
    print("To install missing packages:")
    print(f"pip install {' '.join(missing)}")
else:
    print()
    print("✅ All required packages are installed!")

# Test Django
try:
    import django
    print()
    print(f"Django Version: {django.get_version()}")
    print("Django Location:", django.__file__)
except ImportError:
    print()
    print("❌ Django not available")

print()
print("=" * 50)
