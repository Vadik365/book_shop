#!/bin/sh
set -e


if [ -n "$POSTGRES_HOST" ]; then
  echo "Waiting for PostgreSQL at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
  until nc -z "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"; do
    sleep 0.5
  done
  echo "PostgreSQL is up."
fi

if [ -n "$REDIS_HOST" ]; then
  echo "Waiting for Redis at $REDIS_HOST:${REDIS_PORT:-6379}..."
  until nc -z "$REDIS_HOST" "${REDIS_PORT:-6379}"; do
    sleep 0.5
  done
  echo "Redis is up."
fi

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting: $@"
exec "$@"