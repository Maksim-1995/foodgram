#!/bin/bash

set -e

# Ожидание готовности PostgreSQL
echo "Ожидание готовности базы данных..."
while ! python -c "import psycopg2; psycopg2.connect(
    host='${DB_HOST:-db}',
    port='${DB_PORT:-5432}',
    dbname='${POSTGRES_DB}',
    user='${POSTGRES_USER}',
    password='${POSTGRES_PASSWORD}'
)" 2>/dev/null; do
    echo "База данных ещё не готова, ждём..."
    sleep 1
done
echo "База данных готова!"

# Применяем миграции
python manage.py migrate --noinput

# Собираем статику Django (без --clear, чтобы не удалять файлы фронтенда)
python manage.py collectstatic --noinput

# Загружаем теги (если их нет)
python manage.py load_tags

# Загружаем ингредиенты (если их нет)
python manage.py load_ingredients

exec "$@"