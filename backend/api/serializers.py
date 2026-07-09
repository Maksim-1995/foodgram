import base64
import binascii
import uuid

from core.constants import (
    EMAIL_MAX_LENGTH,
    INGREDIENT_NAME_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT,
    RECIPE_NAME_MAX_LENGTH,
    TAG_NAME_MAX_LENGTH,
    TAG_SLUG_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.core.validators import RegexValidator
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Поле для base64-картинок от фронтенда."""

    def to_internal_value(self, data):
        """Преобразует base64-строку в файл изображения."""
        if isinstance(data, str):
            file_format = 'jpg'

            if ';base64,' in data:
                header, data = data.split(';base64,', 1)
                if '/' in header:
                    file_format = header.rsplit('/', 1)[-1].lower()

            try:
                decoded_file = base64.b64decode(data, validate=True)
            except (TypeError, ValueError, binascii.Error):
                raise serializers.ValidationError(
                    'Некорректная строка base64.'
                )

            file_name = f'{uuid.uuid4()}.{file_format}'
            data = ContentFile(decoded_file, name=file_name)

        return super().to_internal_value(data)

    def to_representation(self, value):
        """Возвращает URL изображения."""
        if not value:
            return None
        return value.url


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = fields

    def get_avatar(self, obj):
        """Возвращает URL аватара пользователя."""
        if obj.avatar:
            return f'/media/{obj.avatar.name}'
        return None

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на автора."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user,
            author=obj,
        ).exists()


class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        validators=(
            UniqueValidator(queryset=User.objects.all()),
        ),
    )
    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH,
        validators=(
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='Недопустимые символы.',
            ),
            UniqueValidator(queryset=User.objects.all()),
        ),
    )
    first_name = serializers.CharField(max_length=USER_NAME_MAX_LENGTH)
    last_name = serializers.CharField(max_length=USER_NAME_MAX_LENGTH)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('id',)

    def validate_username(self, value):
        """Проверяет, что username не равен 'me'."""
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Имя "me" запрещено.'
            )
        return value

    def validate_password(self, value):
        """Проверяет пароль на соответствие требованиям Django."""
        validate_password(value)
        return value

    def create(self, validated_data):
        """Создаёт пользователя с зашифрованным паролем."""
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=TAG_NAME_MAX_LENGTH)
    slug = serializers.SlugField(max_length=TAG_SLUG_MAX_LENGTH)

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = fields


class IngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=INGREDIENT_NAME_MAX_LENGTH)
    measurement_unit = serializers.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
    )

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_AMOUNT)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields

    def get_image(self, obj):
        """Возвращает URL изображения рецепта."""
        if obj.image:
            return obj.image.url
        return None


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = fields

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def _user_has_relation(self, obj, related_name):
        """Проверяет наличие связи пользователя с рецептом."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return getattr(obj, related_name).filter(user=request.user).exists()

    def get_is_favorited(self, obj):
        """Проверяет, находится ли рецепт в избранном у пользователя."""
        return self._user_has_relation(obj, 'favorites')

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, находится ли рецепт в списке покупок у пользователя."""
        return self._user_has_relation(obj, 'shopping_carts')


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField(required=False)
    name = serializers.CharField(max_length=RECIPE_NAME_MAX_LENGTH)
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_tags(self, tags):
        """Проверяет, что теги не пустые и не повторяются."""
        if not tags:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один тег.'
            )

        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.'
            )

        return tags

    def validate_ingredients(self, ingredients):
        """Проверяет, что ингредиенты не пустые и не повторяются."""
        if not ingredients:
            raise serializers.ValidationError(
                'Нужно добавить хотя бы один '
                'ингредиент.'
            )

        ingredient_ids = [item['id'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны '
                'повторяться.'
            )

        return ingredients

    def validate(self, attrs):
        """Проверяет наличие обязательных полей при обновлении рецепта."""
        if self.instance is None:
            return attrs

        required_fields = (
            'ingredients',
            'tags',
            'name',
            'text',
            'cooking_time',
        )
        errors = {
            field: ['Обязательное поле.']
            for field in required_fields
            if field not in self.initial_data
        }
        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def _save_recipe_ingredients(self, recipe, ingredients):
        """Создаёт связи рецепта с ингредиентами."""
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount'],
            )
            for item in ingredients
        )

    def create(self, validated_data):
        """Создаёт рецепт с тегами и ингредиентами."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._save_recipe_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт, перезаписывая теги и ингредиенты."""
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        if tags is not None:
            instance.tags.set(tags)
        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            self._save_recipe_ingredients(instance, ingredients)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Возвращает полное представление рецепта после записи."""
        return RecipeReadSerializer(instance, context=self.context).data


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = fields

    def get_recipes(self, obj):
        """Возвращает рецепты пользователя с учётом параметра recipes_limit."""
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = None

        if request is not None:
            recipes_limit = request.query_params.get('recipes_limit')

        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
            except (TypeError, ValueError):
                recipes_limit = None

        if recipes_limit is not None and recipes_limit >= 0:
            recipes = recipes[:recipes_limit]

        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов пользователя."""
        return obj.recipes.count()


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, attrs):
        """Проверяет, что подписка возможна (не на себя, не повторная)."""
        user = attrs['user']
        author = attrs['author']

        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого '
                'себя.'
            )

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого '
                'пользователя.'
            )

        return attrs

    def to_representation(self, instance):
        """Возвращает данные автора с рецептами после подписки."""
        return UserWithRecipesSerializer(
            instance.author,
            context=self.context,
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, attrs):
        """Проверяет, что рецепт ещё не в избранном."""
        if Favorite.objects.filter(
            user=attrs['user'],
            recipe=attrs['recipe'],
        ).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return attrs

    def to_representation(self, instance):
        """Возвращает упрощённые данные рецепта после добавления."""
        return RecipeMinifiedSerializer(
            instance.recipe,
            context=self.context,
        ).data


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля."""

    new_password = serializers.CharField(write_only=True)
    current_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        """Проверяет, что текущий пароль введён верно."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль.')
        return value

    def validate_new_password(self, value):
        """Проверяет новый пароль на соответствие требованиям Django."""
        validate_password(value)
        return value

    def save(self):
        """Сохраняет новый пароль пользователя."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=('password',))
        return user


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, attrs):
        """Проверяет, что рецепт ещё не в списке покупок."""
        if ShoppingCart.objects.filter(
            user=attrs['user'],
            recipe=attrs['recipe'],
        ).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в список '
                'покупок.'
            )
        return attrs

    def to_representation(self, instance):
        """Возвращает упрощённые данные рецепта после добавления."""
        return RecipeMinifiedSerializer(
            instance.recipe,
            context=self.context,
        ).data
