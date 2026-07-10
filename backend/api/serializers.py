import base64
import binascii
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from rest_framework import serializers
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Поле для base64-картинок от фронтенда."""

    def to_internal_value(self, data):
        """Преобразует base64-строку в файл изображения."""
        if isinstance(data, str):
            file_format = 'jpg'

            if ';base64,' in data:
                header, base64_str = data.split(';base64,', 1)
                if '/' in header:
                    file_format = header.rsplit('/', 1)[-1].lower()
            else:
                base64_str = data

            try:
                decoded_file = base64.b64decode(base64_str, validate=True)
            except (TypeError, ValueError, binascii.Error) as err:
                raise serializers.ValidationError(
                    'Некорректная строка base64.'
                ) from err

            file_uuid = uuid.uuid4()
            file_name = f'{file_uuid}.{file_format}'
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
        if request is None or not request.user.is_authenticated:
            return False
        return request.user.subscriptions.filter(
            author_id=obj.pk,
        ).exists()


class UserCreateSerializer(serializers.ModelSerializer):
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
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = fields


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True,
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class BaseRecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор рецепта с общим полем image."""

    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        """Возвращает URL изображения рецепта."""
        if obj.image:
            return obj.image.url
        return None


class RecipeMinifiedSerializer(BaseRecipeSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class RecipeReadSerializer(BaseRecipeSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def get_is_favorited(self, obj):
        """Проверяет, находится ли рецепт в избранном у пользователя.

        Если queryset был проаннотирован во viewset — возвращает
        готовое значение (один запрос на весь список).
        Иначе выполняет отдельный запрос (N+1).
        """
        if hasattr(obj, 'is_favorited'):
            return obj.is_favorited
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, находится ли рецепт в списке покупок у пользователя.

        Если queryset был проаннотирован во viewset — возвращает
        готовое значение (один запрос на весь список).
        Иначе выполняет отдельный запрос (N+1).
        """
        if hasattr(obj, 'is_in_shopping_cart'):
            return obj.is_in_shopping_cart
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return obj.shopping_carts.filter(user=request.user).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        allow_empty=False,
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    name = serializers.CharField()
    cooking_time = serializers.IntegerField(min_value=1)

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
        """Проверяет, что теги не повторяются."""
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
                'Нужно добавить хотя бы один ингредиент.'
            )

        ingredient_ids = [item['id'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return ingredients

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
        recipe = super().create(validated_data)
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
            instance.recipe_ingredients.clear()
            self._save_recipe_ingredients(instance, ingredients)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Возвращает полное представление рецепта после записи."""
        return RecipeReadSerializer(instance, context=self.context).data


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True,
    )

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


class BaseRecipeRelationSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для связи пользователя с рецептом.

    Используется как предок для FavoriteSerializer и ShoppingCartSerializer.
    """

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    not_found_message = 'Запись не найдена.'
    already_exists_message = 'Запись уже существует.'

    class Meta:
        fields = ('user', 'recipe')

    def validate(self, attrs):
        """Проверяет существование/отсутствие связи."""
        user = self.context['request'].user
        recipe = attrs['recipe']
        is_delete = self.context.get('is_delete', False)
        exists = self.Meta.model.objects.filter(
            user=user, recipe=recipe,
        ).exists()

        if is_delete and not exists:
            raise serializers.ValidationError(self.not_found_message)
        if not is_delete and exists:
            raise serializers.ValidationError(self.already_exists_message)

        return attrs

    def to_representation(self, instance):
        """Возвращает упрощённые данные рецепта после добавления."""
        return RecipeMinifiedSerializer(
            instance.recipe,
            context=self.context,
        ).data


class FavoriteSerializer(BaseRecipeRelationSerializer):
    not_found_message = 'Рецепт не в избранном.'
    already_exists_message = 'Рецепт уже добавлен в избранное.'

    class Meta(BaseRecipeRelationSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(BaseRecipeRelationSerializer):
    not_found_message = 'Рецепт не в списке покупок.'
    already_exists_message = 'Рецепт уже добавлен в список покупок.'

    class Meta(BaseRecipeRelationSerializer.Meta):
        model = ShoppingCart


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


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки пользователя на автора."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    not_found_message = 'Вы не подписаны на этого пользователя.'
    already_exists_message = 'Вы уже подписаны на этого пользователя.'

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, attrs):
        """Проверяет подписку: не на себя и существует/отсутствует."""
        user = self.context['request'].user
        author = attrs['author']

        if not self.context.get('is_delete', False):
            if user == author:
                raise serializers.ValidationError(
                    'Нельзя подписаться на самого себя.'
                )

        exists = Subscription.objects.filter(
            user=user, author=author,
        ).exists()

        if self.context.get('is_delete', False) and not exists:
            raise serializers.ValidationError(self.not_found_message)
        if not self.context.get('is_delete', False) and exists:
            raise serializers.ValidationError(self.already_exists_message)

        return attrs

    def to_representation(self, instance):
        """Возвращает данные автора с рецептами после подписки."""
        return UserWithRecipesSerializer(
            instance.author,
            context=self.context,
        ).data