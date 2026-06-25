from django.contrib import admin
from django.db import models
from django.utils.safestring import mark_safe

from .models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
    Subscription,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', 'recipe_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipe_count=models.Count('recipe_ingredients')
        )

    @admin.display(description='Используется в рецептах')
    def recipe_count(self, obj):
        return obj.recipe_count


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    autocomplete_fields = ('ingredient',)
    fields = ('ingredient', 'amount')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorites_count', 'display_image')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags',)
    filter_horizontal = ('tags',)
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('pub_date', 'favorites_count', 'display_image')
    fieldsets = (
        (None, {
            'fields': (
                'author',
                'name',
                'text',
                'cooking_time',
                'image',
                'display_image',
            )
        }),
        ('Теги и ингредиенты', {
            'fields': ('tags',)
        }),
        ('Дополнительно', {
            'fields': ('pub_date', 'favorites_count')
        }),
    )

    def favorites_count(self, recipe):
        return recipe.favorites.count()
    favorites_count.short_description = 'Число добавлений в избранное'

    def display_image(self, recipe):
        if recipe.image:
            return mark_safe(f'<img src="{recipe.image.url}" width="100" />')
        return 'Нет изображения'
    display_image.short_description = 'Превью'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', 'created_at')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', 'created_at')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author', 'created_at')
    search_fields = ('user__username', 'author__username')
