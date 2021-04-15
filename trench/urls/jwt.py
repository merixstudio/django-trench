from django.urls import path

from trench.views import MFAFirstStepJWTView, MFASecondStepJWTView


urlpatterns = [
    path("login/", MFAFirstStepJWTView.as_view(), name="generate-code"),
    path("login/code/", MFASecondStepJWTView.as_view(), name="generate-token"),
]
