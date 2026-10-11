#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Collect static files into STATIC_ROOT
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate
