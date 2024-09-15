#!/bin/sh

echo "Applying database migrations"
python manage.py migrate

echo "Starting server"
gunicorn --bind 0.0.0.0:8000 satori_video.wsgi
