from rest_framework import generics

from loaninteresttypes.models import LoanInterestType
from loaninteresttypes.serializers import LoanInterestTypeSerializer
from accounts.permissions import IsSystemAdminOrReadOnly


class LoanInterestTypeListCreateView(generics.ListCreateAPIView):
    queryset = LoanInterestType.objects.all()
    serializer_class = LoanInterestTypeSerializer
    permission_classes = [
        IsSystemAdminOrReadOnly,
    ]


class LoanInterestTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = LoanInterestType.objects.all()
    serializer_class = LoanInterestTypeSerializer
    permission_classes = [
        IsSystemAdminOrReadOnly,
    ]
    lookup_field = "reference"
