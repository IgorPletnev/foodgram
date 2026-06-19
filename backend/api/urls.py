from rest_framework.routers import DefaultRouter

from django.urls import path, include

from .views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
    UserViewSet,
    UserAvatarView,
    UserSubscribeView,
)

router_v1 = DefaultRouter()
router_v1.register('users', UserViewSet, basename='user')
router_v1.register('tags', TagViewSet, basename='tag')
router_v1.register('ingredients', IngredientViewSet, basename='ingredient')
router_v1.register('recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('users/me/avatar/', UserAvatarView.as_view(), name='user-avatar'),
    path(
        'users/<int:pk>/subscribe/',
        UserSubscribeView.as_view(),
        name='user-unsubscribe',
    ),
    path('', include(router_v1.urls)),
]