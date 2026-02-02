"""
URL configuration for sea_saw_server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("api/auth/dj/", include("dj_rest_auth.urls")),
    path("api/auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/sea-saw-crm/", include("sea_saw_crm.urls")),
    path("api/attachments/", include("sea_saw_attachment.urls")),  # Attachment endpoints
    path("api/auth/", include("sea_saw_auth.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/download/", include("download.urls")),
    path("api/preference/", include("preference.urls")),
    re_path(r"^auth/", include("djoser.urls")),
]

# Only serve media files directly in development
# In production, use secure download view with permission checks
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# debug_toolbar.middleware.DebugToolbarMiddleware相关配置
urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
