from django.urls import path

from loanapplications.views import LoanApplicationCreateView, LoanProjectionPreviewView

app_name = "loanapplications"

urlpatterns = [
    path("create/", LoanApplicationCreateView.as_view(), name="create"),
    path("preview/", LoanProjectionPreviewView.as_view(), name="preview"),
]
