from django.conf.urls import include
from django.contrib import admin
from django.urls import re_path

from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title='Django-Trench')

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^auth/', include('trench.urls')),
    re_path(r'^auth/jwt/', include('trench.urls.jwt')),
    re_path(r'^auth/token/', include('trench.urls.authtoken')),
    re_path(r'^swagger/', schema_view)
]
