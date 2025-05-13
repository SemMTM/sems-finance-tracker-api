from django.contrib import admin
from django.urls import path, include
from core.views import (ChangeEmailView,
                        CustomUserDetailsView)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.views.generic import TemplateView
from django.conf import settings
from django.urls import re_path
from django.views.static import serve as static_serve
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path("dj-rest-auth/user/", CustomUserDetailsView.as_view()),
    path('dj-rest-auth/registration/',
         include('dj_rest_auth.registration.urls')),
    path('accounts/', include('allauth.urls')),
    path('api/token/', TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(),
         name='token_refresh'),
    path('', include('transactions.urls')),
    path('change-email/', ChangeEmailView.as_view(), name='change_email'),
    path("signin/", TemplateView.as_view(template_name="index.html")),
    path("signup/", TemplateView.as_view(template_name="index.html")),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^assets/(?P<path>.*)$', static_serve, {
            'document_root': BASE_DIR / 'frontend' / 'build' / 'assets'
        }),
    ]
