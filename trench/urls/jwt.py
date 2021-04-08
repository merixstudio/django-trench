from django.urls import re_path

from trench.views import simplejwt as views


urlpatterns = [
    re_path(
        r"^login/$",
        views.JSONWebTokenLoginOrRequestMFACode.as_view(),
        name="generate-code",
    ),
    re_path(
        r"^login/code/",
        views.JSONWebTokenLoginWithMFACode.as_view(),
        name="generate-token",
    ),
]
