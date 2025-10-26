from rest_framework import generics

from loanproducts.serializers import LoanProductSerializer
from loanproducts.models import LoanProduct
from accounts.permissions import IsSystemAdminOrReadOnly


class LoanProductListCreateView(generics.ListCreateAPIView):
    queryset = LoanProduct.objects.all()
    serializer_class = LoanProductSerializer
    permission_classes = [
        IsSystemAdminOrReadOnly,
    ]


class LoanProductDetailView(generics.RetrieveUpdateAPIView):
    queryset = LoanProduct.objects.all()
    serializer_class = LoanProductSerializer
    permission_classes = [
        IsSystemAdminOrReadOnly,
    ]
    lookup_field = "reference"
