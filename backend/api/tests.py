import base64
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase
from users.models import Subscription, User


def _create_test_image():
    """Создаёт тестовое изображение и возвращает его в формате base64."""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f'data:image/jpeg;base64,{encoded}'


def _create_simple_image():
    """Создаёт тестовое изображение как SimpleUploadedFile."""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile(
        'test.jpg',
        buffer.read(),
        content_type='image/jpeg',
    )


class UserModelTest(TestCase):
    """Тесты модели User."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            password='TestPass123!',
        )

    def test_user_creation(self):
        """Проверка создания пользователя."""
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(str(self.user), 'testuser')

    def test_user_email_unique(self):
        """Проверка уникальности email."""
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='test@example.com',
                username='another',
                first_name='Another',
                last_name='User',
                password='TestPass123!',
            )

    def test_user_username_unique(self):
        """Проверка уникальности username."""
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='another@example.com',
                username='testuser',
                first_name='Another',
                last_name='User',
                password='TestPass123!',
            )

    def test_user_avatar_default(self):
        """Проверка, что аватар по умолчанию None."""
        self.assertIsNone(self.user.avatar.name) if self.user.avatar else None


class TagModelTest(TestCase):
    """Тесты модели Tag."""

    def setUp(self):
        self.tag = Tag.objects.create(name='Завтрак', slug='breakfast')

    def test_tag_creation(self):
        """Проверка создания тега."""
        self.assertEqual(Tag.objects.count(), 1)
        self.assertEqual(self.tag.name, 'Завтрак')
        self.assertEqual(self.tag.slug, 'breakfast')
        self.assertEqual(str(self.tag), 'Завтрак')

    def test_tag_name_unique(self):
        """Проверка уникальности названия тега."""
        with self.assertRaises(Exception):
            Tag.objects.create(name='Завтрак', slug='another')

    def test_tag_slug_unique(self):
        """Проверка уникальности slug тега."""
        with self.assertRaises(Exception):
            Tag.objects.create(name='Обед', slug='breakfast')


class IngredientModelTest(TestCase):
    """Тесты модели Ingredient."""

    def setUp(self):
        self.ingredient = Ingredient.objects.create(
            name='Сахар',
            measurement_unit='г',
        )

    def test_ingredient_creation(self):
        """Проверка создания ингредиента."""
        self.assertEqual(Ingredient.objects.count(), 1)
        self.assertEqual(self.ingredient.name, 'Сахар')
        self.assertEqual(self.ingredient.measurement_unit, 'г')
        self.assertEqual(str(self.ingredient), 'Сахар (г)')

    def test_ingredient_unique_constraint(self):
        """Проверка unique_together для name и measurement_unit."""
        with self.assertRaises(Exception):
            Ingredient.objects.create(
                name='Сахар',
                measurement_unit='г',
            )


class RecipeModelTest(TestCase):
    """Тесты модели Recipe."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='author@example.com',
            username='author',
            first_name='Author',
            last_name='Test',
            password='TestPass123!',
        )
        self.tag = Tag.objects.create(name='Десерт', slug='dessert')
        self.ingredient = Ingredient.objects.create(
            name='Сахар',
            measurement_unit='г',
        )
        self.recipe = Recipe.objects.create(
            author=self.user,
            name='Тестовый рецепт',
            image=_create_simple_image(),
            text='Описание рецепта',
            cooking_time=30,
        )
        self.recipe.tags.add(self.tag)
        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            amount=100,
        )

    def test_recipe_creation(self):
        """Проверка создания рецепта."""
        self.assertEqual(Recipe.objects.count(), 1)
        self.assertEqual(self.recipe.name, 'Тестовый рецепт')
        self.assertEqual(self.recipe.author, self.user)
        self.assertEqual(str(self.recipe), 'Тестовый рецепт')

    def test_recipe_tags(self):
        """Проверка связи рецепта с тегами."""
        self.assertIn(self.tag, self.recipe.tags.all())

    def test_recipe_ingredients(self):
        """Проверка связи рецепта с ингредиентами."""
        self.assertIn(self.ingredient, self.recipe.ingredients.all())

    def test_recipe_short_code_generated(self):
        """Проверка генерации короткого кода."""
        self.assertIsNotNone(self.recipe.short_code)
        self.assertEqual(len(self.recipe.short_code), 8)

    def test_recipe_ordering(self):
        """Проверка сортировки рецептов по дате создания (новые сверху)."""
        recipe2 = Recipe.objects.create(
            author=self.user,
            name='Второй рецепт',
            image=_create_simple_image(),
            text='Описание',
            cooking_time=15,
        )
        recipes = Recipe.objects.all()
        self.assertEqual(recipes[0], recipe2)
        self.assertEqual(recipes[1], self.recipe)


class SubscriptionModelTest(TestCase):
    """Тесты модели Subscription."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            first_name='User',
            last_name='Test',
            password='TestPass123!',
        )
        self.author = User.objects.create_user(
            email='author@example.com',
            username='author',
            first_name='Author',
            last_name='Test',
            password='TestPass123!',
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            author=self.author,
        )

    def test_subscription_creation(self):
        """Проверка создания подписки."""
        self.assertEqual(Subscription.objects.count(), 1)
        self.assertEqual(str(self.subscription), 'user подписан на author')

    def test_subscription_unique(self):
        """Проверка уникальности подписки."""
        with self.assertRaises(Exception):
            Subscription.objects.create(
                user=self.user,
                author=self.author,
            )

    def test_subscription_self_not_allowed(self):
        """Проверка запрета подписки на себя."""
        with self.assertRaises(Exception):
            Subscription.objects.create(
                user=self.user,
                author=self.user,
            )


class FavoriteModelTest(TestCase):
    """Тесты модели Favorite."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            first_name='User',
            last_name='Test',
            password='TestPass123!',
        )
        self.author = User.objects.create_user(
            email='author@example.com',
            username='author',
            first_name='Author',
            last_name='Test',
            password='TestPass123!',
        )
        self.recipe = Recipe.objects.create(
            author=self.author,
            name='Рецепт',
            image=_create_simple_image(),
            text='Описание',
            cooking_time=20,
        )
        self.favorite = Favorite.objects.create(
            user=self.user,
            recipe=self.recipe,
        )

    def test_favorite_creation(self):
        """Проверка создания избранного."""
        self.assertEqual(Favorite.objects.count(), 1)
        self.assertEqual(str(self.favorite), 'user - Рецепт')

    def test_favorite_unique(self):
        """Проверка уникальности избранного."""
        with self.assertRaises(Exception):
            Favorite.objects.create(
                user=self.user,
                recipe=self.recipe,
            )


class ShoppingCartModelTest(TestCase):
    """Тесты модели ShoppingCart."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            first_name='User',
            last_name='Test',
            password='TestPass123!',
        )
        self.author = User.objects.create_user(
            email='author@example.com',
            username='author',
            first_name='Author',
            last_name='Test',
            password='TestPass123!',
        )
        self.recipe = Recipe.objects.create(
            author=self.author,
            name='Рецепт',
            image=_create_simple_image(),
            text='Описание',
            cooking_time=20,
        )
        self.cart_item = ShoppingCart.objects.create(
            user=self.user,
            recipe=self.recipe,
        )

    def test_shopping_cart_creation(self):
        """Проверка создания записи в списке покупок."""
        self.assertEqual(ShoppingCart.objects.count(), 1)

    def test_shopping_cart_unique(self):
        """Проверка уникальности записи в списке покупок."""
        with self.assertRaises(Exception):
            ShoppingCart.objects.create(
                user=self.user,
                recipe=self.recipe,
            )


class UserAPITest(APITestCase):
    """Тесты API для пользователей."""

    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'StrongPass123!',
        }
        self.user = User.objects.create_user(
            email='existing@example.com',
            username='existing',
            first_name='Existing',
            last_name='User',
            password='StrongPass123!',
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_user_registration(self):
        """Проверка регистрации нового пользователя."""
        self.client.credentials()
        response = self.client.post(
            '/api/users/',
            self.user_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], self.user_data['email'])
        self.assertEqual(response.data['username'], self.user_data['username'])
        self.assertNotIn('password', response.data)

    def test_user_registration_with_existing_email(self):
        """Проверка регистрации с существующим email."""
        self.client.credentials()
        data = self.user_data.copy()
        data['email'] = 'existing@example.com'
        response = self.client.post('/api/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_with_existing_username(self):
        """Проверка регистрации с существующим username."""
        self.client.credentials()
        data = self.user_data.copy()
        data['username'] = 'existing'
        response = self.client.post('/api/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_with_me_username(self):
        """Проверка регистрации с username 'me'."""
        self.client.credentials()
        data = self.user_data.copy()
        data['username'] = 'me'
        response = self.client.post('/api/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_token(self):
        """Проверка получения токена."""
        self.client.credentials()
        response = self.client.post(
            '/api/auth/token/login/',
            {'email': 'existing@example.com', 'password': 'StrongPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.data)

    def test_get_user_list(self):
        """Проверка получения списка пользователей."""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_get_user_detail(self):
        """Проверка получения конкретного пользователя."""
        response = self.client.get(f'/api/users/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_get_me(self):
        """Проверка получения своего профиля."""
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_get_me_unauthorized(self):
        """Проверка, что неавторизованный не может получить свой профиль."""
        self.client.credentials()
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_set_password(self):
        """Проверка смены пароля."""
        response = self.client.post(
            '/api/users/set_password/',
            {
                'new_password': 'NewStrongPass456!',
                'current_password': 'StrongPass123!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_set_password_wrong_current(self):
        """Проверка смены пароля с неверным текущим паролем."""
        response = self.client.post(
            '/api/users/set_password/',
            {
                'new_password': 'NewStrongPass456!',
                'current_password': 'WrongPassword!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_password_unauthorized(self):
        """Проверка, что неавторизованный не может сменить пароль."""
        self.client.credentials()
        response = self.client.post(
            '/api/users/set_password/',
            {
                'new_password': 'NewStrongPass456!',
                'current_password': 'StrongPass123!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_avatar(self):
        """Проверка загрузки аватара."""
        image_b64 = _create_test_image()
        response = self.client.put(
            '/api/users/me/avatar/',
            {'avatar': image_b64},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('avatar', response.data)

    def test_delete_avatar(self):
        """Проверка удаления аватара."""
        response = self.client.delete('/api/users/me/avatar/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_avatar_unauthorized(self):
        """Проверка, что неавторизованный не может загрузить аватар."""
        self.client.credentials()
        response = self.client.put(
            '/api/users/me/avatar/',
            {'avatar': _create_test_image()},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SubscriptionAPITest(APITestCase):
    """Тесты API для подписок."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            first_name='User',
            last_name='Test',
            password='StrongPass123!',
        )
        self.author = User.objects.create_user(
            email='author@example.com',
            username='author',
            first_name='Author',
            last_name='Test',
            password='StrongPass123!',
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_subscribe_to_user(self):
        """Проверка подписки на пользователя."""
        response = self.client.post(
            f'/api/users/{self.author.id}/subscribe/',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Subscription.objects.filter(
                user=self.user,
                author=self.author,
            ).exists(),
        )

    def test_subscribe_to_self(self):
        """Проверка запрета подписки на себя."""
        response = self.client.post(
            f'/api/users/{self.user.id}/subscribe/',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscribe_twice(self):
        """Проверка запрета повторной подписки."""
        Subscription.objects.create(user=self.user, author=self.author)
        response = self.client.post(
            f'/api/users/{self.author.id}/subscribe/',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsubscribe(self):
        """Проверка отписки от пользователя."""
        Subscription.objects.create(user=self.user, author=self.author)
        response = self.client.delete(
            f'/api/users/{self.author.id}/subscribe/',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Subscription.objects.filter(
                user=self.user,
                author=self.author,
            ).exists(),
        )

    def test_unsubscribe_not_subscribed(self):
        """Проверка отписки, когда не был подписан."""
        response = self.client.delete(
            f'/api/users/{self.author.id}/subscribe/',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscribe_unauthorized(self):
        """Проверка, что неавторизованный не может подписаться."""
        self.client.credentials()
        response = self.client.post(
            f'/api/users/{self.author.id}/subscribe/',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_subscriptions_list(self):
        """Проверка получения списка подписок."""
        Subscription.objects.create(user=self.user, author=self.author)
        response = self.client.get('/api/users/subscriptions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_subscriptions_list_unauthorized(self):
        """Проверка, что неавторизованный не может получить подписки."""
        self.client.credentials()
        response = self.client.get('/api/users/subscriptions/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TagAPITest(APITestCase):
    """Тесты API для тегов."""

    def setUp(self):
        self.client = APIClient()
        self.tag = Tag.objects.create(name='Завтрак', slug='breakfast')
        Tag.objects.create(name='Обед', slug='lunch')

    def test_get_tags_list(self):
        """Проверка получения списка тегов."""
        response = self.client.get('/api/tags/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_tag_detail(self):
        """Проверка получения конкретного тега."""
        response = self.client.get(f'/api/tags/{self.tag.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Завтрак')
        self.assertEqual(response.data['slug'], 'breakfast')

    def test_tags_available_for_unauthorized(self):
        """Проверка, что теги доступны без авторизации."""
        self.client.credentials()
        response = self.client.get('/api/tags/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class IngredientAPITest(APITestCase):
    """Тесты API для ингредиентов."""

    def setUp(self):
        self.client = APIClient()
        self.ingredient = Ingredient.objects.create(
            name='Сахар',
            measurement_unit='г',
        )
        Ingredient.objects.create(
            name='Соль',
            measurement_unit='г',
        )
        Ingredient.objects.create(
            name='Молоко',
            measurement_unit='мл',
        )

    def test_get_ingredients_list(self):
        """Проверка получения списка ингредиентов."""
        response = self.client.get('/api/ingredients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_get_ingredient_detail(self):
        """Проверка получения конкретного ингредиента."""
        response = self.client.get(
            f'/api/ingredients/{self.ingredient.id}/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Сахар')

    def test_ingredient_search_by_name(self):
        """Проверка поиска ингредиента по началу названия."""
        response = self.client.get('/api/ingredients/?name=Са')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Сахар')

    def test_ingredient_search_case_insensitive(self):
        """Проверка регистронезависимого поиска (для латиницы)."""
        Ingredient.objects.create(
            name='Milk',
            measurement_unit='ml',
        )
        response = self.client.get('/api/ingredients/?name=mil')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Milk')

    def test_ingredient_search_no_results(self):
        """Проверка поиска без результатов."""
        response = self.client.get('/api/ingredients/?name=xyz')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_ingredients_available_for_unauthorized(self):
        """Проверка, что ингредиенты доступны без авторизации."""
        self.client.credentials()
        response = self.client.get('/api/ingredients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RecipeAPITest(APITestCase):
    """Тесты API для рецептов."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            first_name='User',
            last_name='Test',
            password='StrongPass123!',
        )
        self.author = User.objects.create_user(
            email='author@example.com',
            username='author',
            first_name='Author',
            last_name='Test',
            password='StrongPass123!',
        )
        self.token = Token.objects.create(user=self.user)
        self.author_token = Token.objects.create(user=self.author)
        self.tag1 = Tag.objects.create(name='Завтрак', slug='breakfast')
        self.tag2 = Tag.objects.create(name='Обед', slug='lunch')
        self.ingredient1 = Ingredient.objects.create(
            name='Сахар',
            measurement_unit='г',
        )
        self.ingredient2 = Ingredient.objects.create(
            name='Молоко',
            measurement_unit='мл',
        )

        self.recipe = Recipe.objects.create(
            author=self.author,
            name='Авторский рецепт',
            image=_create_simple_image(),
            text='Описание рецепта',
            cooking_time=30,
        )
        self.recipe.tags.add(self.tag1, self.tag2)
        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient1,
            amount=100,
        )
        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient2,
            amount=200,
        )

        self.valid_recipe_data = {
            'name': 'Новый рецепт',
            'text': 'Подробное описание',
            'cooking_time': 45,
            'tags': [self.tag1.id, self.tag2.id],
            'ingredients': [
                {'id': self.ingredient1.id, 'amount': 150},
                {'id': self.ingredient2.id, 'amount': 300},
            ],
            'image': _create_test_image(),
        }

    def test_get_recipes_list(self):
        """Проверка получения списка рецептов."""
        response = self.client.get('/api/recipes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_recipe_detail(self):
        """Проверка получения конкретного рецепта."""
        response = self.client.get(f'/api/recipes/{self.recipe.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Авторский рецепт')
        self.assertIn('author', response.data)
        self.assertIn('ingredients', response.data)
        self.assertIn('tags', response.data)

    def test_get_recipe_detail_anonymous(self):
        """Проверка, что рецепт доступен анонимному пользователю."""
        self.client.credentials()
        response = self.client.get(f'/api/recipes/{self.recipe.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_recipe_authenticated(self):
        """Проверка создания рецепта авторизованным пользователем."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        response = self.client.post(
            '/api/recipes/',
            self.valid_recipe_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Новый рецепт')
        self.assertEqual(Recipe.objects.count(), 2)

    def test_create_recipe_anonymous(self):
        """Проверка, что аноним не может создать рецепт."""
        self.client.credentials()
        response = self.client.post(
            '/api/recipes/',
            self.valid_recipe_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_recipe_without_tags(self):
        """Проверка создания рецепта без тегов."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        data = self.valid_recipe_data.copy()
        data['tags'] = []
        response = self.client.post('/api/recipes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_without_ingredients(self):
        """Проверка создания рецепта без ингредиентов."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        data = self.valid_recipe_data.copy()
        data['ingredients'] = []
        response = self.client.post('/api/recipes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_duplicate_ingredients(self):
        """Проверка создания рецепта с дублирующимися ингредиентами."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        data = self.valid_recipe_data.copy()
        data['ingredients'] = [
            {'id': self.ingredient1.id, 'amount': 100},
            {'id': self.ingredient1.id, 'amount': 200},
        ]
        response = self.client.post('/api/recipes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_duplicate_tags(self):
        """Проверка создания рецепта с дублирующимися тегами."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        data = self.valid_recipe_data.copy()
        data['tags'] = [self.tag1.id, self.tag1.id]
        response = self.client.post('/api/recipes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recipe_by_author(self):
        """Проверка обновления рецепта автором."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.author_token.key}',
        )
        update_data = {
            'name': 'Обновлённый рецепт',
            'text': 'Обновлённое описание',
            'cooking_time': 60,
            'tags': [self.tag1.id, self.tag2.id],
            'ingredients': [
                {'id': self.ingredient1.id, 'amount': 200},
                {'id': self.ingredient2.id, 'amount': 300},
            ],
            'image': _create_test_image(),
        }
        response = self.client.patch(
            f'/api/recipes/{self.recipe.id}/',
            update_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.name, 'Обновлённый рецепт')

    def test_update_recipe_by_non_author(self):
        """Проверка, что не-автор не может обновить рецепт."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        response = self.client.patch(
            f'/api/recipes/{self.recipe.id}/',
            {'name': 'Хакнутый рецепт'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_recipe_by_author(self):
        """Проверка удаления рецепта автором."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.author_token.key}',
        )
        response = self.client.delete(f'/api/recipes/{self.recipe.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Recipe.objects.count(), 0)

    def test_delete_recipe_by_non_author(self):
        """Проверка, что не-автор не может удалить рецепт."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        response = self.client.delete(f'/api/recipes/{self.recipe.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_recipe_anonymous(self):
        """Проверка, что аноним не может удалить рецепт."""
        self.client.credentials()
        response = self.client.delete(f'/api/recipes/{self.recipe.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_recipe_link(self):
        """Проверка получения короткой ссылки на рецепт."""
        response = self.client.get(
            f'/api/recipes/{self.recipe.id}/get-link/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('short-link', response.data)
        self.assertIn(
            f'/s/{self.recipe.short_code}/',
            response.data['short-link'],
        )

    def test_filter_recipes_by_author(self):
        """Проверка фильтрации рецептов по автору."""
        response = self.client.get(
            f'/api/recipes/?author={self.author.id}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_recipes_by_tag(self):
        """Проверка фильтрации рецептов по тегу."""
        response = self.client.get(
            f'/api/recipes/?tags={self.tag1.slug}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_recipes_by_multiple_tags(self):
        """Проверка фильтрации по нескольким тегам (OR)."""
        tag3 = Tag.objects.create(name='Ужин', slug='dinner')
        response = self.client.get(
            f'/api/recipes/?tags={self.tag1.slug}&tags={tag3.slug}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_recipes_by_is_favorited(self):
        """Проверка фильтрации по избранному."""
        Favorite.objects.create(user=self.user, recipe=self.recipe)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        response = self.client.get('/api/recipes/?is_favorited=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_recipes_by_is_in_shopping_cart(self):
        """Проверка фильтрации по списку покупок."""
        ShoppingCart.objects.create(user=self.user, recipe=self.recipe)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        response = self.client.get('/api/recipes/?is_in_shopping_cart=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class RecipeFavoriteShoppingCartTest(APITestCase):
    """Тесты для избранного и списка покупок."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            first_name='User',
            last_name='Test',
            password='StrongPass123!',
        )
        self.author = User.objects.create_user(
            email='author@example.com',
            username='author',
            first_name='Author',
            last_name='Test',
            password='StrongPass123!',
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.tag = Tag.objects.create(name='Завтрак', slug='breakfast')
        self.ingredient = Ingredient.objects.create(
            name='Сахар',
            measurement_unit='г',
        )
        self.recipe = Recipe.objects.create(
            author=self.author,
            name='Рецепт',
            image=_create_simple_image(),
            text='Описание',
            cooking_time=20,
        )
        self.recipe.tags.add(self.tag)
        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            amount=100,
        )

    def test_add_to_favorites(self):
        """Проверка добавления рецепта в избранное."""
        response = self.client.post(
            f'/api/recipes/{self.recipe.id}/favorite/',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Favorite.objects.filter(
                user=self.user,
                recipe=self.recipe,
            ).exists(),
        )

    def test_add_to_favorites_twice(self):
        """Проверка запрета повторного добавления в избранное."""
        Favorite.objects.create(user=self.user, recipe=self.recipe)
        response = self.client.post(
            f'/api/recipes/{self.recipe.id}/favorite/',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_from_favorites(self):
        """Проверка удаления рецепта из избранного."""
        Favorite.objects.create(user=self.user, recipe=self.recipe)
        response = self.client.delete(
            f'/api/recipes/{self.recipe.id}/favorite/',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Favorite.objects.filter(
                user=self.user,
                recipe=self.recipe,
            ).exists(),
        )

    def test_remove_from_favorites_not_in_list(self):
        """Проверка удаления из избранного, когда рецепта там нет."""
        response = self.client.delete(
            f'/api/recipes/{self.recipe.id}/favorite/',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_favorite_unauthorized(self):
        """Проверка, что неавторизованный не может добавить в избранное."""
        self.client.credentials()
        response = self.client.post(
            f'/api/recipes/{self.recipe.id}/favorite/',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_to_shopping_cart(self):
        """Проверка добавления рецепта в список покупок."""
        response = self.client.post(
            f'/api/recipes/{self.recipe.id}/shopping_cart/',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            ShoppingCart.objects.filter(
                user=self.user,
                recipe=self.recipe,
            ).exists(),
        )

    def test_add_to_shopping_cart_twice(self):
        """Проверка запрета повторного добавления в список покупок."""
        ShoppingCart.objects.create(user=self.user, recipe=self.recipe)
        response = self.client.post(
            f'/api/recipes/{self.recipe.id}/shopping_cart/',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_from_shopping_cart(self):
        """Проверка удаления рецепта из списка покупок."""
        ShoppingCart.objects.create(user=self.user, recipe=self.recipe)
        response = self.client.delete(
            f'/api/recipes/{self.recipe.id}/shopping_cart/',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            ShoppingCart.objects.filter(
                user=self.user,
                recipe=self.recipe,
            ).exists(),
        )

    def test_remove_from_shopping_cart_not_in_list(self):
        """Проверка удаления из списка покупок, когда рецепта там нет."""
        response = self.client.delete(
            f'/api/recipes/{self.recipe.id}/shopping_cart/',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_shopping_cart_unauthorized(self):
        """Проверка, что неавторизованный не может добавить в покупки."""
        self.client.credentials()
        response = self.client.post(
            f'/api/recipes/{self.recipe.id}/shopping_cart/',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_download_shopping_cart(self):
        """Проверка скачивания списка покупок."""
        ShoppingCart.objects.create(user=self.user, recipe=self.recipe)
        response = self.client.get('/api/recipes/download_shopping_cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response['Content-Type'],
            'text/plain; charset=utf-8',
        )
        self.assertIn('Сахар', response.content.decode('utf-8'))

    def test_download_shopping_cart_unauthorized(self):
        """Проверка, что неавторизованный не может скачать список."""
        self.client.credentials()
        response = self.client.get('/api/recipes/download_shopping_cart/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_download_shopping_cart_ingredients_summed(self):
        """Проверка суммирования ингредиентов в списке покупок."""
        recipe2 = Recipe.objects.create(
            author=self.author,
            name='Второй рецепт',
            image=_create_simple_image(),
            text='Описание',
            cooking_time=15,
        )
        recipe2.tags.add(self.tag)
        RecipeIngredient.objects.create(
            recipe=recipe2,
            ingredient=self.ingredient,
            amount=200,
        )
        ShoppingCart.objects.create(user=self.user, recipe=self.recipe)
        ShoppingCart.objects.create(user=self.user, recipe=recipe2)

        response = self.client.get('/api/recipes/download_shopping_cart/')
        content = response.content.decode('utf-8')
        self.assertIn('Сахар (г) — 300', content)
