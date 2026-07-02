from django.core.management.base import BaseCommand

from recipes.models import Tag


TAGS = [
    {'name': 'Завтрак', 'slug': 'breakfast'},
    {'name': 'Обед', 'slug': 'lunch'},
    {'name': 'Ужин', 'slug': 'dinner'},
]


class Command(BaseCommand):
    help = 'Загружает теги в БД.'

    def handle(self, *args, **options):
        created_count = 0
        for tag_data in TAGS:
            _, created = Tag.objects.get_or_create(
                slug=tag_data['slug'],
                defaults=tag_data,
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Загрузка тегов завершена. Создано: {created_count}'
            )
        )