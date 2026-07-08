import secrets

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


def make_image(name):
    """Создаёт минимальный валидный PNG 1x1 px."""
    return ContentFile(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00'
        b'\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT'
        b'\x08\xd7c\xf8\x0f\x00\x00\x00\x00\xff\xff\x03\x00\x00\x00'
        b'\x04\x00\x01\x00\x00\x00\x00\x00',
        name=name,
    )


def _create_recipe(
    author, recipe_data, tags_dict, ingredients_dict, image_name, self,
):
    """Создаёт один рецепт с ингредиентами и тегами."""
    tag_objects = [
        tags_dict[slug]
        for slug in recipe_data['tags_slugs']
        if slug in tags_dict
    ]

    recipe, created = Recipe.objects.get_or_create(
        name=recipe_data['name'],
        author=author,
        defaults={
            'text': recipe_data['text'],
            'cooking_time': recipe_data['cooking_time'],
            'image': make_image(image_name),
            'short_code': secrets.token_hex(4),
        },
    )

    if created:
        recipe.tags.set(tag_objects)
        for ing_name, amount in recipe_data['ingredients_data']:
            ing = ingredients_dict.get(ing_name)
            if ing:
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ing,
                    amount=amount,
                )
        self.stdout.write(
            self.style.SUCCESS(
                f'  Создан рецепт: "{recipe.name}" (автор: {author.username})'
            )
        )
    else:
        self.stdout.write(
            self.style.WARNING(
                f'  Рецепт "{recipe.name}" уже существует'
            )
        )


class Command(BaseCommand):
    help = (
        'Создаёт 7 тестовых пользователей с рецептами '
        'и PNG-картинками для демонстрации.'
    )

    def handle(self, *args, **options):
        # 1. Теги
        tags_data = [
            {'name': 'Завтрак', 'slug': 'breakfast'},
            {'name': 'Обед', 'slug': 'lunch'},
            {'name': 'Ужин', 'slug': 'dinner'},
        ]
        tags = {}
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                slug=tag_data['slug'],
                defaults=tag_data,
            )
            tags[tag.slug] = tag
            if created:
                self.stdout.write(f'  Создан тег: {tag.name}')

        self.stdout.write(self.style.SUCCESS('Теги загружены.'))

        # 2. Ингредиенты (если ещё не загружены через load_ingredients)
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
            ing, created = Ingredient.objects.get_or_create(
                name=ing_data['name'],
                measurement_unit=ing_data['measurement_unit'],
            )
            ingredients[ing.name] = ing

        self.stdout.write(self.style.SUCCESS('Ингредиенты загружены.'))

        # 3. Пользователи (7 шт.)
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
            {
                'email': 'elena_cook@example.com',
                'username': 'elena_cook',
                'first_name': 'Елена',
                'last_name': 'Васильева',
                'password': 'ElenaPass456',
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
                    self.style.SUCCESS(f'  Создан пользователь: {user.email}')
                )
            else:
                # Обновляем поля на случай если пользователь уже был
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
                self.stdout.write(
                    self.style.WARNING(
                        f'  Пользователь {user.email} обновлён'
                    )
                )
            users[user.username] = user

        users_count = len(users)
        self.stdout.write(
            self.style.SUCCESS(
                f'Создано/обновлено пользователей: {users_count}'
            )
        )

        # 4. Рецепты для каждого пользователя
        # Рецепты для admin (2 рецепта)
        admin_recipes = [
            {
                'name': 'Блины классические',
                'text': (
                    'Классические тонкие блины — отличный вариант для '
                    'завтрака или ужина. Подавайте со сметаной, вареньем '
                    'или мёдом.'
                ),
                'cooking_time': 30,
                'tags_slugs': ['breakfast', 'dinner'],
                'ingredients_data': [
                    ('Молоко', 500),
                    ('Яйцо куриное', 3),
                    ('Мука пшеничная', 250),
                    ('Сахар', 30),
                    ('Соль', 1),
                    ('Масло растительное', 3),
                ],
            },
            {
                'name': 'Глазунья с луком',
                'text': (
                    'Простая и сытная яичница-глазунья с репчатым луком — '
                    'идеальный завтрак за 10 минут.'
                ),
                'cooking_time': 10,
                'tags_slugs': ['breakfast'],
                'ingredients_data': [
                    ('Яйцо куриное', 3),
                    ('Лук репчатый', 60),
                    ('Масло растительное', 2),
                    ('Соль', 1),
                ],
            },
        ]
        admin_user = users.get('admin')
        if admin_user is None:
            self.stdout.write(self.style.ERROR('Пользователь admin не найден'))
        else:
            for recipe_index, recipe_data in enumerate(admin_recipes):
                _create_recipe(
                    admin_user, recipe_data,
                    tags, ingredients,
                    f'admin_recipe_{recipe_index}.png', self,
                )

        # Рецепт для user1 (Иван)
        user1_obj = users.get('user1')
        if user1_obj is not None:
            _create_recipe(
                user1_obj,
                {
                    'name': 'Картофельное пюре',
                    'text': (
                        'Классическое картофельное пюре — '
                        'отличный гарнир к любому блюду.'
                    ),
                    'cooking_time': 30,
                    'tags_slugs': ['lunch', 'dinner'],
                    'ingredients_data': [
                        ('Картофель', 500),
                        ('Молоко', 150),
                        ('Соль', 1),
                        ('Масло растительное', 2),
                    ],
                },
                tags, ingredients, 'user1_potato.png', self,
            )
        else:
            self.stdout.write(self.style.ERROR('Пользователь user1 не найден'))

        # Рецепт для user2 (Мария)
        user2_obj = users.get('user2')
        if user2_obj is not None:
            _create_recipe(
                user2_obj,
                {
                    'name': 'Яичница с овощами',
                    'text': (
                        'Простой и быстрый завтрак из яиц с овощами.'
                    ),
                    'cooking_time': 15,
                    'tags_slugs': ['breakfast'],
                    'ingredients_data': [
                        ('Яйцо куриное', 3),
                        ('Лук репчатый', 50),
                        ('Масло растительное', 1),
                        ('Соль', 1),
                    ],
                },
                tags, ingredients, 'user2_eggs.png', self,
            )
        else:
            self.stdout.write(self.style.ERROR('Пользователь user2 не найден'))

        # Рецепт для user3 (Алексей)
        user3_obj = users.get('user3')
        if user3_obj is not None:
            _create_recipe(
                user3_obj,
                {
                    'name': 'Суп картофельный',
                    'text': (
                        'Сытный картофельный суп — идеальный обед.'
                    ),
                    'cooking_time': 45,
                    'tags_slugs': ['lunch'],
                    'ingredients_data': [
                        ('Картофель', 300),
                        ('Морковь', 100),
                        ('Лук репчатый', 80),
                        ('Чеснок', 2),
                        ('Соль', 1),
                    ],
                },
                tags, ingredients, 'user3_soup.png', self,
            )
        else:
            self.stdout.write(self.style.ERROR('Пользователь user3 не найден'))

        # Рецепты для chef_olga (3 рецепта)
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
            },
            {
                'name': 'Солянка сборная мясная',
                'text': (
                    'Насыщенный ароматный суп с несколькими видами мяса — '
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
            },
        ]
        chef_olga_user = users.get('chef_olga')
        if chef_olga_user is None:
            self.stdout.write(self.style.ERROR('Пользователь chef_olga не найден'))
        else:
            for recipe_index, recipe_data in enumerate(olga_recipes):
                _create_recipe(
                    chef_olga_user, recipe_data,
                    tags, ingredients,
                    f'olga_recipe_{recipe_index}.png', self,
                )

        # Рецепты для chef_dmitry (3 рецепта)
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
            },
        ]
        chef_dmitry_user = users.get('chef_dmitry')
        if chef_dmitry_user is None:
            self.stdout.write(self.style.ERROR('Пользователь chef_dmitry не найден'))
        else:
            for recipe_index, recipe_data in enumerate(dmitry_recipes):
                _create_recipe(
                    chef_dmitry_user, recipe_data,
                    tags, ingredients,
                    f'dmitry_recipe_{recipe_index}.png', self,
                )

        # Рецепты для elena_cook (2 рецепта)
        elena_recipes = [
            {
                'name': 'Домашние блины',
                'text': (
                    'Румяные и тонкие блины — '
                    'отличный вариант для завтрака.'
                ),
                'cooking_time': 40,
                'tags_slugs': ['breakfast', 'dinner'],
                'ingredients_data': [
                    ('Молоко', 500),
                    ('Яйцо куриное', 2),
                    ('Мука пшеничная', 200),
                    ('Сахар', 30),
                    ('Масло растительное', 2),
                    ('Соль', 1),
                ],
            },
            {
                'name': 'Жареный картофель с луком',
                'text': (
                    'Золотистый жареный картофель с луком — '
                    'простое и вкусное блюдо для обеда или ужина.'
                ),
                'cooking_time': 25,
                'tags_slugs': ['lunch', 'dinner'],
                'ingredients_data': [
                    ('Картофель', 600),
                    ('Лук репчатый', 100),
                    ('Масло растительное', 3),
                    ('Соль', 2),
                    ('Чеснок', 2),
                ],
            },
        ]
        elena_user = users.get('elena_cook')
        if elena_user is None:
            self.stdout.write(self.style.ERROR('Пользователь elena_cook не найден'))
        else:
            for recipe_index, recipe_data in enumerate(elena_recipes):
                _create_recipe(
                    elena_user, recipe_data,
                    tags, ingredients,
                    f'elena_recipe_{recipe_index}.png', self,
                )

        # Итог
        total_recipes = Recipe.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                '═══ ЗАГРУЗКА ТЕСТОВЫХ ДАННЫХ ЗАВЕРШЕНА ═══\n'
                f'Пользователей: {users_count}\n'
                f'Рецептов в БД: {total_recipes}\n'
                'Пароль для admin: admin123\n'
                'Пароль для user1/user2/user3: user12345\n'
                'Пароль для chef_olga: OlgaPass123\n'
                'Пароль для chef_dmitry: DimaPass123\n'
                'Пароль для elena_cook: ElenaPass456\n'
                '═══════════════════════════════════════'
            )
        )
