from django.urls import path

from loaninteresttypes.views import (
    LoanInterestTypeListCreateView,
    LoanInterestTypeDetailView,
)

app_name = "loaninteresttypes"

urlpatterns = [
    path("", LoanInterestTypeListCreateView.as_view(), name="list-create"),
    path("<str:reference>/", LoanInterestTypeDetailView.as_view(), name="detail"),
]
