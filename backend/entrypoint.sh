#!/bin/bash

set -e

# Ожидание готовности PostgreSQL
echo "Ожидание готовности базы данных..."
while ! python3 -c "import psycopg2; psycopg2.connect(
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
python3 manage.py migrate --noinput

# Собираем статику Django (без --clear, чтобы не удалять файлы фронтенда)
python3 manage.py collectstatic --noinput

# Загружаем теги (если их нет)
python3 manage.py load_tags || echo "Предупреждение: load_tags завершился с ошибкой"

# Загружаем ингредиенты (если их нет)
python3 manage.py load_ingredients || echo "Предупреждение: load_ingredients завершился с ошибкой"

# Загружаем тестовые данные: 7 пользователей с рецептами и картинками
python3 manage.py load_test_data || echo "Предупреждение: load_test_data завершился с ошибкой"

exec "$@"
