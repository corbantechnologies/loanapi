from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from loanproducts.models import LoanProduct


class LoanProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        validators=[UniqueValidator(queryset=LoanProduct.objects.all())], required=True
    )
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = LoanProduct
        fields = (
            "name",
            "interest_rate",
            "interest_type",
            "interest_period",
            "calculation_schedule",
            "compounding_frequency",
            "description",
            "currency",
            "created_at",
            "updated_at",
            "reference",
        )
