from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator
from drf_extra_fields.fields import Base64ImageField

from django.contrib.auth import (
    get_user_model,
    authenticate,
    update_session_auth_hash,
)
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


class UserSerializer(serializers.ModelSerializer):
    """Базовый сериализатор пользователя (чтение)."""

    is_subscribed = serializers.BooleanField(read_only=True, default=False)
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

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        if instance.avatar:
            instance.avatar.delete()
        return super().update(instance, validated_data)


class PublicUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для публичной регистрации (без лишних прав)."""

    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
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
        extra_kwargs = {
            'username': {'required': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует'
            )
        return value

    def validate_username(self, value):
        import re
        if not re.match(r'^[\w.@+-]+\Z', value):
            raise serializers.ValidationError(
                'Имя пользователя может содержать только буквы, '
                'цифры и символы . _ @ + -'
            )
        return value

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class AuthorSerializer(serializers.ModelSerializer):
    """Сериализатор автора (пользователя) для вложения в рецепт."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.follower.filter(author=obj).exists()
        return False


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
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
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
        )

    def get_is_favorited(self, obj):
        if hasattr(obj, 'is_favorited'):
            return obj.is_favorited
        return False

    def get_is_in_shopping_cart(self, obj):
        if hasattr(obj, 'is_in_shopping_cart'):
            return obj.is_in_shopping_cart
        return False


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
    image = Base64ImageField(required=True, allow_null=True)
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

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Изображение обязательно для рецепта'
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один тег'
            )
        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                'Теги не должны повторяться'
            )
        return value

    def validate_ingredients(self, value):
        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )
        return value

    def validate(self, attrs):
        """Проверяем, что при PATCH поля ingredients и tags
        обязательны, если они присутствуют в исходном запросе."""
        request = self.context.get('request')
        if request and request.method in ('PATCH', 'PUT'):
            data = request.data
            # Если поле ingredients отсутствует в данных запроса — ошибка
            if 'ingredients' not in data:
                raise serializers.ValidationError(
                    {'ingredients': ['Обязательное поле.']}
                )
            # Если поле tags отсутствует в данных запроса — ошибка
            if 'tags' not in data:
                raise serializers.ValidationError(
                    {'tags': ['Обязательное поле.']}
                )
        return attrs

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
    """Сериализатор для получения короткой ссылки на рецепт."""

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

    def to_representation(self, instance):
        """Заменяем ключ 'short_link' на 'short-link' в ответе API."""
        ret = super().to_representation(instance)
        ret['short-link'] = ret.pop('short_link')
        return ret


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
            ),
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
        except User.MultipleObjectsReturned as err:
            raise ValidationError(
                'Обнаружено несколько учётных записей с таким email'
            ) from err
        except User.DoesNotExist as err:
            raise ValidationError('Неверные учетные данные') from err

        user = authenticate(username=email, password=password)
        if not user:
            raise ValidationError('Неверные учетные данные')
        self.context['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.context['user']
        token, _ = Token.objects.get_or_create(user=user)
        return {'auth_token': token.key}


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = (
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном'
            ),
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
            ),
        )


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise ValidationError('Неверный пароль')
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        update_session_auth_hash(self.context['request'], user)
        return user
