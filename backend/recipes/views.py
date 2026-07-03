from django.shortcuts import get_object_or_404
from django.views.generic.base import RedirectView

from recipes.models import Recipe


class RecipeShortLinkRedirectView(RedirectView):
    """Редирект с короткой ссылки на страницу рецепта."""

    def get_redirect_url(self, *args, **kwargs):
        short_code = kwargs.get('short_code')
        recipe = get_object_or_404(Recipe, short_code=short_code)
        return f'/recipes/{recipe.id}/'
