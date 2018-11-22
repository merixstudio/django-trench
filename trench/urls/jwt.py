from django.conf.urls import url

from trench.views import jwt as views


urlpatterns = [
    url(
        r'^login/$',
        views.JSONWebTokenLoginOrRequestMFACode.as_view(),
        name='generate-code',
    ),
    url(
        r'^login/code/',
        views.JSONWebTokenLoginWithMFACode.as_view(),
        name='generate-token',
    ),
]
