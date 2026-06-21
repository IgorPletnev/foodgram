from django_filters import rest_framework as filters
from recipes.models import Recipe
from django.contrib.auth import get_user_model

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    tags = filters.CharFilter(method='filter_tags')
    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_in_cart')

    def filter_tags(self, queryset, name, value):
        tags_list = self.request.query_params.getlist('tags')
        if not tags_list:
            return queryset
        # Поддержка формата ?tags=slug1,slug2
        if len(tags_list) == 1 and ',' in tags_list[0]:
            tags_list = tags_list[0].split(',')
        tags_list = [t for t in tags_list if t]
        if not tags_list:
            return queryset
        return queryset.filter(tags__slug__in=tags_list).distinct()

    def filter_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                favorites__user=self.request.user
            ).distinct()
        return queryset

    def filter_in_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                shopping_cart__user=self.request.user
            ).distinct()
        return queryset

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')