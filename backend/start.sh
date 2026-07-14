#!/bin/bash

# اجرای میگریشن‌های دیتابیس
echo "Running migrations..."
python manage.py migrate --noinput

# اجرای سلری ورکر در پس‌زمینه (& باعث می‌شود این پروسه در پس‌زمینه برود)
echo "Starting Celery Worker..."
celery -A core worker --loglevel=info &

# اجرای سرور اصلی جنگو در پیش‌زمینه (تا کانتینر روشن بماند)
echo "Starting Gunicorn Web Server..."
gunicorn core.wsgi:application --bind 0.0.0.0:10000
