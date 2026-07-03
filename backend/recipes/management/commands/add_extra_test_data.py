import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


class Command(BaseCommand):
    help = 'Добавляет 2 новых пользователей с 3 рецептами каждый.'

    def handle(self, *args, **options):
        # Загружаем existing теги и ингредиенты
        tags = {t.slug: t for t in Tag.objects.all()}
        ingredients = {i.name: i for i in Ingredient.objects.all()}

        if not tags:
            self.stderr.write(self.style.ERROR(
                'Теги не найдены. Сначала запустите load_tags.'
            ))
            return

        # Маленькие реальные PNG-картинки (1x1 px, с правильной структурой)
        # Каждая будет уникальной благодаря разным именам файлов
        def make_image(name):
            return ContentFile(
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00'
                b'\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT'
                b'\x08\xd7c\xf8\x0f\x00\x00\x00\x00\xff\xff\x03\x00\x00\x00'
                b'\x04\x00\x01\x00\x00\x00\x00\x00',
                name=name,
            )

        users_data = [
            {
                'email': 'chef_olga@example.com',
                'username': 'chef_olga',
                'first_name': 'Ольга',
                'last_name': 'Смирнова',
                'password': 'OlgaPass123',
            },
            {
                'email': 'chef_dmitry@example.com',
                'username': 'chef_dmitry',
                'first_name': 'Дмитрий',
                'last_name': 'Козлов',
                'password': 'DimaPass123',
            },
        ]

        users = {}
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'username': user_data['username'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                },
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Создан пользователь: {user.email}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Пользователь {user.email} уже существует'
                    )
                )
            users[user.username] = user

        # Рецепты для Ольги
        olga_recipes = [
            {
                'name': 'Овощное рагу с картофелем',
                'text': (
                    'Сочное овощное рагу — идеальный вариант для сытного '
                    'обеда. Готовится быстро и просто из доступных продуктов.'
                ),
                'cooking_time': 40,
                'tags_slugs': ['lunch'],
                'ingredients_data': [
                    ('Картофель', 400),
                    ('Морковь', 150),
                    ('Лук репчатый', 100),
                    ('Масло растительное', 3),
                    ('Соль', 2),
                    ('Чеснок', 3),
                ],
                'image_name': 'veg_stew.png',
            },
            {
                'name': 'Сладкие блинчики с яблоками',
                'text': (
                    'Нежные блинчики с яблочной начинкой — отличный завтрак '
                    'для всей семьи. Подавайте со сметаной или вареньем.'
                ),
                'cooking_time': 35,
                'tags_slugs': ['breakfast'],
                'ingredients_data': [
                    ('Молоко', 300),
                    ('Яйцо куриное', 2),
                    ('Мука пшеничная', 180),
                    ('Сахар', 40),
                    ('Соль', 1),
                    ('Масло растительное', 2),
                ],
                'image_name': 'pancakes.png',
            },
            {
                'name': 'Солянка сборная мясная',
                'text': (
                    'Насыщенный и ароматный суп с несколькими видами мяса — '
                    'настоящее украшение праздничного стола.'
                ),
                'cooking_time': 90,
                'tags_slugs': ['lunch', 'dinner'],
                'ingredients_data': [
                    ('Картофель', 300),
                    ('Морковь', 100),
                    ('Лук репчатый', 80),
                    ('Масло растительное', 2),
                    ('Соль', 3),
                    ('Чеснок', 2),
                ],
                'image_name': 'solyanka.png',
            },
        ]

        # Рецепты для Дмитрия
        dmitry_recipes = [
            {
                'name': 'Картофельная запеканка с грибами',
                'text': (
                    'Сытная запеканка из картофеля с шампиньонами и '
                    'золотистой корочкой. Идеально для ужина.'
                ),
                'cooking_time': 50,
                'tags_slugs': ['dinner'],
                'ingredients_data': [
                    ('Картофель', 600),
                    ('Лук репчатый', 100),
                    ('Яйцо куриное', 3),
                    ('Молоко', 100),
                    ('Масло растительное', 3),
                    ('Соль', 2),
                ],
                'image_name': 'casserole.png',
            },
            {
                'name': 'Омлет с сыром и зеленью',
                'text': (
                    'Пышный омлет с расплавленным сыром и свежей зеленью — '
                    'быстрый и полезный завтрак за 10 минут.'
                ),
                'cooking_time': 10,
                'tags_slugs': ['breakfast'],
                'ingredients_data': [
                    ('Яйцо куриное', 4),
                    ('Молоко', 80),
                    ('Соль', 1),
                    ('Масло растительное', 1),
                ],
                'image_name': 'omelette.png',
            },
            {
                'name': 'Борщ классический',
                'text': (
                    'Традиционный красный борщ со свеклой и мясом — '
                    'обязательное блюдо в каждой кулинарной книге.'
                ),
                'cooking_time': 75,
                'tags_slugs': ['lunch'],
                'ingredients_data': [
                    ('Картофель', 400),
                    ('Морковь', 120),
                    ('Лук репчатый', 80),
                    ('Соль', 3),
                    ('Сахар', 10),
                    ('Чеснок', 3),
                    ('Масло растительное', 2),
                ],
                'image_name': 'borsch.png',
            },
        ]

        # Создаём рецепты для Ольги
        for recipe_data in olga_recipes:
            _create_recipe(
                users['chef_olga'], recipe_data,
                tags, ingredients, make_image, self,
            )

        # Создаём рецепты для Дмитрия
        for recipe_data in dmitry_recipes:
            _create_recipe(
                users['chef_dmitry'], recipe_data,
                tags, ingredients, make_image, self,
            )

        self.stdout.write(
            self.style.SUCCESS(
                'Тестовые данные успешно добавлены: 2 пользователя, '
                '6 рецептов.'
            )
        )


def _create_recipe(
    author, recipe_data, tags, ingredients, make_image, self,
):
    tag_objects = [
        tags[slug]
        for slug in recipe_data['tags_slugs']
        if slug in tags
    ]

    recipe, created = Recipe.objects.get_or_create(
        name=recipe_data['name'],
        author=author,
        defaults={
            'text': recipe_data['text'],
            'cooking_time': recipe_data['cooking_time'],
            'image': make_image(recipe_data['image_name']),
            'short_code': uuid.uuid4().hex[:8],
        },
    )

    if created:
        recipe.tags.set(tag_objects)
        for ing_name, amount in recipe_data['ingredients_data']:
            ing = ingredients.get(ing_name)
            if ing:
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ing,
                    amount=amount,
                )
        self.stdout.write(
            self.style.SUCCESS(
                f'Создан рецепт: "{recipe.name}" (автор: {author.username})'
            )
        )
    else:
        self.stdout.write(
            self.style.WARNING(
                f'Рецепт "{recipe.name}" уже существует'
            )
        )
