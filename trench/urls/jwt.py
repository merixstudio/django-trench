from django.urls import path

from trench.views.jwt import MFAFirstStepJWTView, MFASecondStepJWTView


urlpatterns = (
    path("login/", MFAFirstStepJWTView.as_view(), name="generate-code-jwt"),
    path("login/code/", MFASecondStepJWTView.as_view(), name="generate-token-jwt"),
)
