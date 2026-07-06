import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из data/ingredients.json в БД.'

    def handle(self, *args, **options):
        json_path = os.path.join(
            settings.BASE_DIR,
            'data',
            'ingredients.json',
        )

        if not os.path.exists(json_path):
            self.stderr.write(
                self.style.ERROR(f'Файл {json_path} не найден.')
            )
            return

        with open(json_path, 'r', encoding='utf-8') as file:
            ingredients_data = json.load(file)

        created_count = 0
        skipped_count = 0

        for item in ingredients_data:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')

            if not name or not measurement_unit:
                self.stderr.write(
                    self.style.WARNING(
                        f'Пропущена запись с неполными данными: {item}'
                    )
                )
                continue

            _, created = Ingredient.objects.get_or_create(
                name=name,
                measurement_unit=measurement_unit,
            )

            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Загрузка завершена. '
                f'Создано: {created_count}, '
                f'Пропущено (уже есть): {skipped_count}'
            )
        )
