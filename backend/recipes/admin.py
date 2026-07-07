from django.contrib import admin
from django.db.models import Count
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для редактирования ингредиентов рецепта в админке."""

    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ-панель для управления тегами."""

    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админ-панель для управления ингредиентами."""

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ-панель для управления рецептами."""

    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'favorites_count',
    )
    search_fields = ('name', 'author__email', 'author__username')
    list_filter = ('tags',)
    filter_horizontal = ('tags',)
    autocomplete_fields = ('author',)
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        """Аннотирует queryset количеством добавлений в избранное."""
        queryset = super().get_queryset(request)
        return queryset.annotate(total_favorites=Count('favorites'))

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.total_favorites


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админ-панель для управления избранными рецептами."""

    list_display = ('id', 'user', 'recipe', 'created_at')
    search_fields = ('user__email', 'user__username', 'recipe__name')
    autocomplete_fields = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ-панель для управления списком покупок."""

    list_display = ('id', 'user', 'recipe', 'created_at')
    search_fields = ('user__email', 'user__username', 'recipe__name')
    autocomplete_fields = ('user', 'recipe')
