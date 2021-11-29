from django.conf.urls import include
from django.contrib import admin
from django.urls import re_path

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny

from trench import __version__


schema_view = get_schema_view(
    openapi.Info(
        title="Django Trench example app API",
        default_version=__version__,
        description="This example illustrates the usage of Django Trench package",
        contact=openapi.Contact(email="code@merixstudio.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = (
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^auth/", include("trench.urls")),
    re_path(r"^auth/jwt/", include("trench.urls.jwt")),
    re_path(r"^auth/token/", include("trench.urls.authtoken")),
    re_path(
        r"^swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
)
