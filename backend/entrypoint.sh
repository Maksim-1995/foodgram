#!/bin/bash

set -e

# Применяем миграции
python manage.py migrate --noinput

# Собираем статику Django (без --clear, чтобы не удалять файлы фронтенда)
python manage.py collectstatic --noinput

# Загружаем теги (если их нет)
python manage.py load_tags

# Загружаем ингредиенты (если их нет)
python manage.py load_ingredients

exec "$@"