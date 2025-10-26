from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from loaninteresttypes.models import LoanInterestType


class LoanInterestTypeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        validators=[UniqueValidator(queryset=LoanInterestType.objects.all())]
    )

    class Meta:
        model = LoanInterestType
        fields = (
            "name",
            "description",
            "created_at",
            "updated_at",
            "reference",
        )
