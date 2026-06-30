from rest_framework.pagination import PageNumberPagination


class FoodgramPagination(PageNumberPagination):
    """Пагинация для Foodgram с кастомным параметром limit."""

    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100