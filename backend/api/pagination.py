from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """Кастомная пагинация с поддержкой параметра `limit`."""
    page_size_query_param = 'limit'
    page_size_query_description = (
        'Количество объектов на странице'
    )