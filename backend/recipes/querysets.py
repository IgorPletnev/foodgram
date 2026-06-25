from django.db import models
from django.db.models import Exists, OuterRef, Value
from django.apps import apps


class RecipeQuerySet(models.QuerySet):

    def with_favorite_flag(self, user):
        if not user.is_authenticated:
            return self.annotate(
                is_favorited=Value(False, output_field=models.BooleanField())
            ).order_by('-pub_date')
        # Получаем модель Favorite
        Favorite = apps.get_model('recipes', 'Favorite')
        return self.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
            )
        ).order_by('-pub_date')

    def with_shopping_cart_flag(self, user):
        if not user.is_authenticated:
            return self.annotate(
                is_in_shopping_cart=Value(
                    False, output_field=models.BooleanField()
                )
            ).order_by('-pub_date')
        # Получаем модель ShoppingCart
        ShoppingCart = apps.get_model('recipes', 'ShoppingCart')
        return self.annotate(
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(user=user, recipe=OuterRef('pk'))
            )
        ).order_by('-pub_date')


class ShoppingCartQuerySet(models.QuerySet):

    def for_user(self, user):
        return self.filter(user=user).select_related('recipe')

    def get_ingredients_summary(self):
        """Агрегирует ингредиенты из корзины пользователя одним запросом."""
        from django.db.models import Sum

        RecipeIngredient = apps.get_model('recipes', 'RecipeIngredient')
        cart_items = self.values_list('recipe_id', flat=True)
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe_id__in=cart_items)
            .values(
                'ingredient_id',
                'ingredient__name',
                'ingredient__measurement_unit',
            )
            .annotate(total=Sum('amount'))
            .order_by('ingredient_id')
        )
        result = {}
        for item in ingredients:
            key = (
                item['ingredient_id'],
                item['ingredient__name'],
                item['ingredient__measurement_unit'],
            )
            result[key] = item['total']
        return result


class FavoriteQuerySet(models.QuerySet):
    """Кастомный QuerySet для модели Favorite."""

    def for_user(self, user):
        return self.filter(user=user).select_related('recipe')
