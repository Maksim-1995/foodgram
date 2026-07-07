import uuid

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
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
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
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from users.models import Subscription, User


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
        if self.action in ('me', 'subscriptions', 'subscribe',
                           'avatar', 'set_password'):
            return (IsAuthenticated(),)
        if self.action == 'create':
            return (AllowAny(),)
        return (AllowAny(),)

    def get_serializer_context(self):
        """Добавляет request в контекст сериализатора."""
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @action(detail=False, methods=('get',), url_path='me')
    def me(self, request):
        """Возвращает профиль текущего пользователя."""
        user = request.user
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('put', 'delete'),
        url_path='me/avatar',
    )
    def avatar(self, request):
        """Загружает или удаляет аватар текущего пользователя."""
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user,
                data=request.data,
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=('post',),
        url_path='set_password',
    )
    def set_password(self, request):
        """Меняет пароль текущего пользователя."""
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя."""
        user = request.user
        queryset = User.objects.filter(subscribers__user=user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page,
                many=True,
                context={'request': request},
            )
            return self.get_paginated_response(serializer.data)
        serializer = UserWithRecipesSerializer(
            queryset,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='subscribe',
    )
    def subscribe(self, request, pk=None):
        """Подписывает или отписывает текущего пользователя от автора."""
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'author': author.id},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user, author=author)
            return Response(
                UserWithRecipesSerializer(
                    author,
                    context={'request': request},
                ).data,
                status=status.HTTP_201_CREATED,
            )

        if request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=user,
                author=author,
            )
            if not subscription.exists():
                return Response(
                    {'errors': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для тегов: только чтение."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингредиентов: только чтение с поиском."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
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

    def get_permissions(self):
        """Возвращает permission classes для actions рецептов."""
        if self.action in ('favorite', 'shopping_cart',
                           'download_shopping_cart'):
            return (IsAuthenticated(),)
        return super().get_permissions()

    def get_serializer_class(self):
        """Возвращает сериализатор: для чтения или для записи."""
        if self.request.method in ('GET',):
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

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        """Генерирует или возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_code = recipe.short_code
        if not short_code:
            short_code = uuid.uuid4().hex[:8]
            recipe.short_code = short_code
            recipe.save(update_fields=('short_code',))
        return Response(
            {'short-link': request.build_absolute_uri(f'/s/{short_code}/')},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='favorite',
    )
    def favorite(self, request, pk=None):
        """Добавляет или удаляет рецепт из избранного."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'recipe': recipe.id},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user, recipe=recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        if request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=user, recipe=recipe)
            if not favorite.exists():
                return Response(
                    {'errors': 'Рецепт не в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет или удаляет рецепт из списка покупок."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data={'recipe': recipe.id},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user, recipe=recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        if request.method == 'DELETE':
            cart_item = ShoppingCart.objects.filter(
                user=user,
                recipe=recipe,
            )
            if not cart_item.exists():
                return Response(
                    {'errors': 'Рецепт не в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=('get',),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Скачивает файл со списком покупок в формате .txt."""
        user = request.user
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_carts__user=user)
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            shopping_list.append(
                f'{ingredient["ingredient__name"]} '
                f'({ingredient["ingredient__measurement_unit"]}) — '
                f'{ingredient["total_amount"]}\n',
            )

        response = HttpResponse(
            shopping_list,
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
