from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    Subscription
)
from .filters import RecipeFilter
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer,
    RecipeShortLinkSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
    SetAvatarSerializer,
    PublicUserCreateSerializer,
    SimpleTokenLoginSerializer,
    SubscriptionSerializer,
    TokenSerializer
)
from .permissions import IsAuthenticatedAuthorOrReadOnly

User = get_user_model()


# ========== Пользователи ==========

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для пользователей (только чтение, кроме подписок и аватара)."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @action(detail=False, url_path='me')
    def me(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=('put',), url_path='me/avatar')
    def update_avatar(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED
            )
        user = request.user
        serializer = SetAvatarSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'avatar': self.get_serializer(user).data.get('avatar')}
        )

    @action(detail=False, methods=('delete',), url_path='me/avatar')
    def delete_avatar(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED
            )
        user = request.user
        if user.avatar:
            user.avatar.delete()
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, url_path='subscriptions')
    def subscriptions(self, request):
        if not request.user.is_authenticated:
            return Response({'results': []}, status=status.HTTP_200_OK)
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = UserWithRecipesSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=('post',), url_path='subscribe')
    def subscribe(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED
            )
        author = get_object_or_404(User, pk=pk)
        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            UserWithRecipesSerializer(
                author, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=('delete',), url_path='subscribe')
    def unsubscribe(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED
            )
        user = request.user
        author = get_object_or_404(User, pk=pk)
        subscription = Subscription.objects.filter(user=user, author=author)
        if not subscription.exists():
            raise ValidationError(
                {'detail': 'Вы не подписаны на этого пользователя'}
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ========== Публичная регистрация ==========

class PublicUserCreateView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = PublicUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


# ========== Кастомный вход по email ==========

class SimpleTokenLoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = SimpleTokenLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        # Используем сериализатор для создания токена
        token_serializer = TokenSerializer(data={'user': user.id})
        token_serializer.is_valid(raise_exception=True)
        token = token_serializer.save()
        return Response({'auth_token': token.key})


# ========== Базовый класс для Tag и Ingredient ==========

class BaseReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    permission_classes = (AllowAny,)

class TagViewSet(BaseReadOnlyViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class IngredientViewSet(BaseReadOnlyViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.none()

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


# ========== Рецепты ==========

class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user,
                        recipe=OuterRef('pk')
                    )
                )
            )
        return queryset

    def get_permissions(self):
        if self.action in {'update', 'partial_update', 'destroy'}:
            return (
                permissions.IsAuthenticated(),
                IsAuthenticatedAuthorOrReadOnly()
            )
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            context['user'] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        output_serializer = RecipeSerializer(
            serializer.instance, context={'request': request}
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def _handle_relation(self, request, model, already_msg):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED
            )
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            _, created = model.objects.get_or_create(user=user, recipe=recipe)
            if not created:
                raise ValidationError({'detail': already_msg})
            serializer = RecipeMinifiedSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # DELETE
        model.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('post', 'delete'), url_path='favorite')
    def favorite(self, request, pk=None):
        return self._handle_relation(
            request, Favorite, 'Рецепт уже в избранном'
        )

    @action(detail=True, methods=('post', 'delete'), url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        return self._handle_relation(
            request, ShoppingCart, 'Рецепт уже в списке покупок'
        )

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        serializer = RecipeShortLinkSerializer(
            recipe, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED
            )
        user = request.user
        cart_recipes = ShoppingCart.objects.filter(
            user=user
        ).select_related('recipe')
        ingredients_dict = {}
        for cart in cart_recipes:
            for ri in cart.recipe.recipe_ingredients.select_related(
                'ingredient'
            ):
                ing = ri.ingredient
                key = (ing.id, ing.name, ing.measurement_unit)
                ingredients_dict[key] = ingredients_dict.get(
                    key, 0
                ) + ri.amount
        lines = [
            f'{name} ({unit}) — {amount}' for (_, name, unit),
            amount in ingredients_dict.items()
        ]
        content = '\n'.join(lines)
        return FileResponse(
            content.encode('utf-8'),
            content_type='text/plain',
            filename='shopping_list.txt'
        )
