from django.urls import path

from loanapplications.views import LoanProjectionView

app_name = "loanapplications"

urlpatterns = [
    path("loan-projection/", LoanProjectionView.as_view(), name="loan-projection"),
]
