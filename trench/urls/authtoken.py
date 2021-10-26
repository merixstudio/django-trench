from django.urls import path

from trench.views.authtoken import MFAFirstStepAuthTokenView, MFASecondStepAuthTokenView


urlpatterns = (
    path("login/", MFAFirstStepAuthTokenView.as_view(), name="generate-code-authtoken"),
    path(
        "login/code/",
        MFASecondStepAuthTokenView.as_view(),
        name="generate-token-authtoken",
    ),
)
