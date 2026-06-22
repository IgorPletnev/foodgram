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
        ingredients = {}
        for cart_item in self.select_related('recipe'):
            for ri in cart_item.recipe.recipe_ingredients.select_related(
                'ingredient'
            ):
                ing = ri.ingredient
                key = (ing.id, ing.name, ing.measurement_unit)
                ingredients[key] = ingredients.get(key, 0) + ri.amount
        return ingredients


class FavoriteQuerySet(models.QuerySet):
    """Кастомный QuerySet для модели Favorite."""

    def for_user(self, user):
        return self.filter(user=user).select_related('recipe')
