#!/bin/sh
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

# Автосоздание суперпользователя из переменных окружения (идемпотентно).
# Задайте на RelaxDev: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD,
# (опционально DJANGO_SUPERUSER_EMAIL) — админ появится/обновится при деплое.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Ensuring superuser '$DJANGO_SUPERUSER_USERNAME'..."
  python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ["DJANGO_SUPERUSER_USERNAME"]
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
user, created = User.objects.get_or_create(username=username, defaults={"email": email})
user.is_staff = True
user.is_superuser = True
user.set_password(password)
if email:
    user.email = email
user.save()
print("superuser", "created" if created else "updated", ":", username)
PY
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn on port ${PORT:-8000}..."
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --access-logfile - \
    --error-logfile -
