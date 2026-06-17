from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from api.views import PublicUserCreateView, SimpleTokenLoginView
from djoser.views import TokenDestroyView
from djoser import urls as djoser_urls

auth_urls = [
    path('token/login/', SimpleTokenLoginView.as_view(), name='login'),
    path('', include(djoser_urls)),
    path('token/logout/', TokenDestroyView.as_view(), name='logout'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('s/<slug:slug>/', RedirectView.as_view(
        url='/recipes/%(slug)s/'
    ), name='short-link'),
    path('api/users/', PublicUserCreateView.as_view(), name='user-create'),
    path('api/', include('api.urls')),
    path('api/auth/', include(auth_urls)),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )