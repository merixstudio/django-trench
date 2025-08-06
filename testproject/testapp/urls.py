from django.conf.urls import include
from django.contrib import admin
from django.urls import re_path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


urlpatterns = (
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^auth/", include("trench.urls")),
    re_path(r"^auth/jwt/", include("trench.urls.jwt")),
    re_path(r"^auth/token/", include("trench.urls.authtoken")),
    re_path(r"^schema/", SpectacularAPIView.as_view(), name="schema"),
    re_path(
        r"^swagger",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    re_path(
        r"^redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
)
