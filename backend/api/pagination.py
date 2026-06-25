from rest_framework.pagination import PageNumberPagination


class PageNumberPaginationWithLimit(PageNumberPagination):
    """Пагинация с поддержкой параметра `limit`."""
    page_size_query_param = 'limit'
    page_size_query_description = (
        'Количество объектов на странице'
    )
