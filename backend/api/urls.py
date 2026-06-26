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

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('users/me/avatar/', UserAvatarView.as_view(), name='user-avatar'),
    path(
        'users/<int:pk>/subscribe/',
        UserSubscribeView.as_view(),
        name='user-unsubscribe',
    ),
    path('', include(router.urls)),
]
