from rest_framework import viewsets, status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.contrib.auth import get_user_model
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
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
    FavoriteSerializer,
    ShoppingCartSerializer,
)
from .permissions import IsAuthenticatedAuthorOrReadOnly

User = get_user_model()

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для пользователей (чтение, подписки, аватар)."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    lookup_field = 'id'
    lookup_url_kwarg = 'pk'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @action(detail=False, url_path='me', permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('put',),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def update_avatar(self, request):
        user = request.user
        serializer = SetAvatarSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'avatar': self.get_serializer(user).data.get('avatar')}
        )

    @action(
        detail=False,
        methods=('delete',),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def delete_avatar(self, request):
        request.user.delete_avatar()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        author_ids = request.user.following.values_list('author', flat=True)
        queryset = User.objects.filter(id__in=author_ids)
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

    @action(
        detail=True,
        methods=('post',),
        url_path='subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk=None):
        author = self.get_object()
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

    @action(
        detail=True,
        methods=('delete',),
        url_path='subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def unsubscribe(self, request, pk=None):
        author = self.get_object()
        request.user.following.filter(author=author).delete()
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
        token, _ = Token.objects.get_or_create(user=user)
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
            queryset = queryset.with_favorite_flag(
                user
            ).with_shopping_cart_flag(user)
        return queryset

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
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

    def _handle_relation(self, request, serializer_class, model):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            serializer = serializer_class(
                data={'user': user.id, 'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                RecipeMinifiedSerializer(
                    recipe, context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        
        model.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='favorite',
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        return self._handle_relation(request, FavoriteSerializer, Favorite)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        return self._handle_relation(
            request, ShoppingCartSerializer, ShoppingCart
        )

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        serializer = RecipeShortLinkSerializer(
            recipe, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients_dict = ShoppingCart.objects.for_user(
            request.user
        ).get_ingredients_summary()
        lines = [f'{name} ({unit}) — {amount}' for (
            _, name, unit
        ), amount in ingredients_dict.items()]
        content = '\n'.join(lines)
        return FileResponse(
            content.encode('utf-8'),
            content_type='text/plain',
            filename='shopping_list.txt'
        )