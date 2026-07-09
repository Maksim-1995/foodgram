from api.filters import IngredientFilter, RecipeFilter
from api.pagination import FoodgramPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    SetPasswordSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)
from django.contrib.auth import get_user_model
from django.db.models import Exists, F, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

User = get_user_model()


class ReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """Базовый ViewSet для read-only эндпоинтов, доступных всем."""
    permission_classes = (AllowAny,)
    pagination_class = None


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet для пользователей: регистрация, профиль, подписки, аватар."""

    queryset = User.objects.all()
    pagination_class = FoodgramPagination
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        """Возвращает сериализатор в зависимости от действия."""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        """Возвращает permission classes в зависимости от действия."""
        if self.action in {'me', 'subscriptions', 'subscribe',
                           'unsubscribe', 'upload_avatar',
                           'delete_avatar', 'set_password'}:
            return (IsAuthenticated(),)
        return super().get_permissions()

    def get_serializer_context(self):
        """Добавляет request в контекст сериализатора."""
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @action(detail=False, url_path='me')
    def me(self, request):
        """Возвращает профиль текущего пользователя."""
        user = request.user
        serializer = UserSerializer(
            user,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('put',),
        url_path='me/avatar',
    )
    def upload_avatar(self, request):
        """Загружает аватар текущего пользователя."""
        user = request.user
        serializer = AvatarSerializer(
            user,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @upload_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаляет аватар текущего пользователя."""
        user = request.user
        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('post',),
        url_path='set_password',
    )
    def set_password(self, request):
        """Меняет пароль текущего пользователя."""
        serializer = SetPasswordSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, url_path='subscriptions')
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя."""
        user = request.user
        queryset = User.objects.filter(subscribers__user=user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page,
                many=True,
                context=self.get_serializer_context(),
            )
            return self.get_paginated_response(serializer.data)
        serializer = UserWithRecipesSerializer(
            queryset,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
        url_path='subscribe',
    )
    def subscribe(self, request, pk=None):
        """Подписывает текущего пользователя на автора."""
        author = get_object_or_404(User, pk=pk)
        user = request.user

        serializer = SubscriptionSerializer(
            data={'author': author.id},
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user, author=author)
        return Response(
            UserWithRecipesSerializer(
                author,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        """Отписывает текущего пользователя от автора."""
        author = get_object_or_404(User, pk=pk)
        user = request.user

        deleted_count, _ = user.subscriptions.filter(
            author=author,
        ).delete()
        if deleted_count == 0:
            raise ValidationError('Вы не подписаны на этого пользователя.')
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyViewSet):
    """ViewSet для тегов: только чтение."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyViewSet):
    """ViewSet для ингредиентов: только чтение с поиском."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов: CRUD, избранное, корзина, ссылка, скачивание."""

    queryset = Recipe.objects.select_related(
        'author',
    ).prefetch_related(
        'tags',
        'recipe_ingredients__ingredient',
    )
    pagination_class = FoodgramPagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        """Аннотирует рецепты полями is_favorited и is_in_shopping_cart.

        Вместо N+1 запросов (по одному на каждый рецепт для каждого поля)
        делает всего 2 подзапроса через Exists, что даёт огромный
        прирост производительности на списках рецептов.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                ),
            )
        else:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(pk__isnull=True)
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(pk__isnull=True)
                ),
            )
        return queryset

    def get_permissions(self):
        """Возвращает permission classes для actions рецептов."""
        if self.action in {'favorite', 'shopping_cart',
                           'download_shopping_cart'}:
            return (IsAuthenticated(),)
        return super().get_permissions()

    def get_serializer_class(self):
        """Возвращает сериализатор: для чтения или для записи."""
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_serializer_context(self):
        """Добавляет request в контекст сериализатора."""
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def perform_create(self, serializer):
        """Устанавливает автором рецепта текущего пользователя."""
        serializer.save(author=self.request.user)

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        """Генерирует или возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_url = request.build_absolute_uri(
            reverse('recipes:recipe_short_link', args=[recipe.short_code])
        )
        return Response({'short-link': short_url})

    @action(
        detail=True,
        methods=('post',),
        url_path='favorite',
    )
    def favorite(self, request, pk=None):
        """Добавляет рецепт в избранное."""
        recipe = self.get_object()
        user = request.user

        serializer = FavoriteSerializer(
            data={'recipe': recipe.id},
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user, recipe=recipe)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        """Удаляет рецепт из избранного."""
        recipe = self.get_object()
        user = request.user

        deleted_count, _ = Favorite.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if deleted_count == 0:
            raise ValidationError('Рецепт не в избранном.')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post',),
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок."""
        recipe = self.get_object()
        user = request.user

        serializer = ShoppingCartSerializer(
            data={'recipe': recipe.id},
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user, recipe=recipe)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @shopping_cart.mapping.delete
    def remove_from_cart(self, request, pk=None):
        """Удаляет рецепт из списка покупок."""
        recipe = self.get_object()
        user = request.user

        deleted_count, _ = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if deleted_count == 0:
            raise ValidationError('Рецепт не в списке покупок.')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Скачивает файл со списком покупок в формате .txt."""
        user = request.user
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_carts__user=user)
            .values(
                name=F('ingredient__name'),
                unit=F('ingredient__measurement_unit'),
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('name')
        )

        shopping_list = 'Список покупок:\n' + ''.join(
            f'{ing["name"]} ({ing["unit"]}) — {ing["total_amount"]}\n'
            for ing in ingredients
        )

        response = HttpResponse(
            shopping_list,
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
