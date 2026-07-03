import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


class Command(BaseCommand):
    help = 'Создаёт тестовых пользователей и рецепты.'

    def handle(self, *args, **options):
        # Создаём теги, если их нет
        tags_data = [
            {'name': 'Завтрак', 'slug': 'breakfast'},
            {'name': 'Обед', 'slug': 'lunch'},
            {'name': 'Ужин', 'slug': 'dinner'},
        ]
        tags = {}
        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(
                slug=tag_data['slug'],
                defaults=tag_data,
            )
            tags[tag.slug] = tag

        # Базовые ингредиенты (если ещё не загружены)
        ingredients_data = [
            {'name': 'Картофель', 'measurement_unit': 'г'},
            {'name': 'Морковь', 'measurement_unit': 'г'},
            {'name': 'Лук репчатый', 'measurement_unit': 'г'},
            {'name': 'Соль', 'measurement_unit': 'по вкусу'},
            {'name': 'Сахар', 'measurement_unit': 'г'},
            {'name': 'Молоко', 'measurement_unit': 'мл'},
            {'name': 'Яйцо куриное', 'measurement_unit': 'шт.'},
            {'name': 'Масло растительное', 'measurement_unit': 'ст. л.'},
            {'name': 'Мука пшеничная', 'measurement_unit': 'г'},
            {'name': 'Чеснок', 'measurement_unit': 'зубчик'},
        ]
        ingredients = {}
        for ing_data in ingredients_data:
            ing, _ = Ingredient.objects.get_or_create(
                name=ing_data['name'],
                measurement_unit=ing_data['measurement_unit'],
            )
            ingredients[ing.name] = ing

        # Тестовые пользователи
        users_data = [
            {
                'email': 'admin@example.com',
                'username': 'admin',
                'first_name': 'Администратор',
                'last_name': 'Системы',
                'password': 'admin123',
                'is_staff': True,
            },
            {
                'email': 'user1@example.com',
                'username': 'user1',
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'password': 'user12345',
            },
            {
                'email': 'user2@example.com',
                'username': 'user2',
                'first_name': 'Мария',
                'last_name': 'Петрова',
                'password': 'user12345',
            },
            {
                'email': 'user3@example.com',
                'username': 'user3',
                'first_name': 'Алексей',
                'last_name': 'Сидоров',
                'password': 'user12345',
            },
        ]

        users = {}
        for user_data in users_data:
            email = user_data['email']
            username = user_data['username']
            first_name = user_data['first_name']
            last_name = user_data['last_name']
            password = user_data['password']
            is_staff = user_data.get('is_staff', False)

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                },
            )
            if created:
                user.set_password(password)
                user.is_staff = is_staff
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Создан пользователь: {user.email}'
                    )
                )
            else:
                # Update fields if user already exists
                changed = False
                if user.username != username:
                    user.username = username
                    changed = True
                if user.first_name != first_name:
                    user.first_name = first_name
                    changed = True
                if user.last_name != last_name:
                    user.last_name = last_name
                    changed = True
                if user.is_staff != is_staff:
                    user.is_staff = is_staff
                    changed = True
                if changed:
                    user.save()
                user.set_password(password)
                user.save(update_fields=('password',))
            users[user.username] = user

        # Тестовые рецепты
        test_image = ContentFile(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00'
            b'\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT'
            b'\x08\xd7c\xf8\x0f\x00\x00\x00\x00\xff\xff\x03\x00\x00\x00'
            b'\x04\x00\x01\x00\x00\x00\x00\x00',
            name='test.png',
        )

        recipes_data = [
            {
                'author': users['user1'],
                'name': 'Картофельное пюре',
                'text': ('Классическое картофельное пюре — '
                         'отличный гарнир к любому блюду.'),
                'cooking_time': 30,
                'tags': [tags['lunch'], tags['dinner']],
                'ingredients': [
                    (ingredients['Картофель'], 500),
                    (ingredients['Молоко'], 150),
                    (ingredients['Соль'], 1),
                    (ingredients['Масло растительное'], 2),
                ],
            },
            {
                'author': users['user2'],
                'name': 'Яичница с овощами',
                'text': ('Простой и быстрый завтрак '
                         'из яиц с овощами.'),
                'cooking_time': 15,
                'tags': [tags['breakfast']],
                'ingredients': [
                    (ingredients['Яйцо куриное'], 3),
                    (ingredients['Лук репчатый'], 50),
                    (ingredients['Масло растительное'], 1),
                    (ingredients['Соль'], 1),
                ],
            },
            {
                'author': users['user3'],
                'name': 'Домашние блины',
                'text': ('Румяные и тонкие блины — '
                         'отличный вариант для завтрака.'),
                'cooking_time': 40,
                'tags': [tags['breakfast'], tags['dinner']],
                'ingredients': [
                    (ingredients['Молоко'], 500),
                    (ingredients['Яйцо куриное'], 2),
                    (ingredients['Мука пшеничная'], 200),
                    (ingredients['Сахар'], 30),
                    (ingredients['Масло растительное'], 2),
                    (ingredients['Соль'], 1),
                ],
            },
            {
                'author': users['user1'],
                'name': 'Суп картофельный',
                'text': ('Сытный картофельный суп — '
                         'идеальный обед.'),
                'cooking_time': 45,
                'tags': [tags['lunch']],
                'ingredients': [
                    (ingredients['Картофель'], 300),
                    (ingredients['Морковь'], 100),
                    (ingredients['Лук репчатый'], 80),
                    (ingredients['Чеснок'], 2),
                    (ingredients['Соль'], 1),
                ],
            },
        ]

        for recipe_data in recipes_data:
            ingredients_list = recipe_data.pop('ingredients')
            tags_list = recipe_data.pop('tags')

            recipe, created = Recipe.objects.get_or_create(
                name=recipe_data['name'],
                author=recipe_data['author'],
                defaults={
                    'text': recipe_data['text'],
                    'cooking_time': recipe_data['cooking_time'],
                    'image': test_image,
                    'short_code': uuid.uuid4().hex[:8],
                },
            )
            if created:
                recipe.tags.set(tags_list)
                for ingredient, amount in ingredients_list:
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredient,
                        amount=amount,
                    )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Создан рецепт: {recipe.name} '
                        f'(автор: {recipe.author.username})'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS('Тестовые данные успешно загружены.')
        )
