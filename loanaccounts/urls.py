from django.urls import path

from loanproducts.views import LoanProductListCreateView, LoanProductDetailView

app_name = "loanproducts"

urlpatterns = [
    path("", LoanProductListCreateView.as_view(), name="loanproducts"),
    path(
        "<str:reference>/", LoanProductDetailView.as_view(), name="loanproduct-detail"
    ),
]
