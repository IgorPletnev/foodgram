from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator
from drf_extra_fields.fields import Base64ImageField

from django.contrib.auth import get_user_model, authenticate
from django.urls import reverse

from recipes.fields import AbsoluteUrlImageField
from recipes.models import (  # noqa: F401, I001
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
    Subscription,
)

User = get_user_model()


# ========== Пользовательские сериализаторы ==========

class UserSerializer(serializers.ModelSerializer):
    """Базовый сериализатор пользователя (чтение)."""

    is_subscribed = serializers.BooleanField(read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_avatar(self, user):
        if user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(user.avatar.url)
        return None


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор пользователя с его рецептами (для подписок)."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, user):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None
        recipes_qs = user.recipes.all()
        if limit and limit.isdigit():
            recipes_qs = recipes_qs[:int(limit)]
        serializer = RecipeMinifiedSerializer(
            recipes_qs, many=True, context={'request': request}
        )
        return serializer.data


class SetAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара."""

    avatar = serializers.ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        # Удаляем старый файл аватара, если он есть
        if instance.avatar:
            instance.avatar.delete()
        return super().update(instance, validated_data)


class PublicUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для публичной регистрации (без лишних прав)."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


# ========== Сериализаторы для тегов, ингредиентов, рецептов ==========

class AuthorSerializer(serializers.ModelSerializer):
    """Сериализатор автора (пользователя) для вложения в рецепт."""

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'avatar',
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('id',)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = AbsoluteUrlImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    image = AbsoluteUrlImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
            'pub_date',
        )


class IngredientItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f'Ингредиент с id {value} не существует'
            )
        return value


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientItemSerializer(many=True, allow_empty=False)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'ingredients',
        )

    def _clear_ingredients(self, recipe):
        recipe.recipe_ingredients.all().delete()

    def _save_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['id'],
                amount=item['amount']
            )
            for item in ingredients_data
        ])

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)
        instance = super().update(instance, validated_data)
        if tags is not None:
            instance.tags.set(tags)
        if ingredients_data is not None:
            self._clear_ingredients(instance)
            self._save_ingredients(instance, ingredients_data)
        return instance


class RecipeShortLinkSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('short_link',)

    def get_short_link(self, recipe):
        request = self.context.get('request')
        path = reverse('short-link', args=[recipe.short_link_slug])
        if request:
            return request.build_absolute_uri(path)
        return path


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки (валидация подписки на себя и дублей)."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = (
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны'
            )
        )

    def validate(self, attrs):
        user = attrs['user']
        author = attrs['author']
        if user == author:
            raise ValidationError({'detail': 'Нельзя подписаться на себя'})
        return attrs


class TokenSerializer(serializers.ModelSerializer):
    """Сериализатор для создания токена аутентификации."""

    class Meta:
        model = Token
        fields = ('user',)


class SimpleTokenLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as err:
            raise ValidationError('Неверные учетные данные') from err
        user = authenticate(username=user.username, password=password)
        if not user:
            raise ValidationError('Неверные учетные данные')
        return {'user': user}
    

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = (
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном'
            )
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = (
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в списке покупок'
            )
        )