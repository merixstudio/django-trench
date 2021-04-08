from django.urls import path

from trench.views import simplejwt as views


urlpatterns = [
    path(
        "login/",
        views.JSONWebTokenLoginOrRequestMFACode.as_view(),
        name="generate-code",
    ),
    path(
        "login/code/",
        views.JSONWebTokenLoginWithMFACode.as_view(),
        name="generate-token",
    ),
]
