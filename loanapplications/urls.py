from django.urls import path

from loanapplications.views import FlatRateProjectionView, DiminishingProjectionView, CompoundProjectionView

app_name = "loanapplications"

urlpatterns = [
    path("flat/", FlatRateProjectionView.as_view(), name="flat-projection"),
    path(
        "diminishing/",
        DiminishingProjectionView.as_view(),
        name="diminishing-projection",
    ),
    path(
        "compound/", CompoundProjectionView.as_view(), name="compound-projection"
    ),
]
