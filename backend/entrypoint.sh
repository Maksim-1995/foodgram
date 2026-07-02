#!/bin/bash

set -e

# Применяем миграции
python manage.py migrate --noinput

# Собираем статику (на случай если не собралась на этапе build)
python manage.py collectstatic --noinput --clear

# Загружаем теги (если их нет)
python manage.py load_tags

# Загружаем ингредиенты (если их нет)
python manage.py load_ingredients

exec "$@"