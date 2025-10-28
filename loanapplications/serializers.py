# serializers.py
from rest_framework import serializers
from loanproducts.models import LoanProduct
from loanapplications.models import LoanApplication


class LoanApplicationSerializer(serializers.Serializer):
    product = serializers.SlugRelatedField(
        slug_field="name",
        queryset=LoanProduct.objects.filter(is_active=True),
    )
    requested_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, min_value=1
    )

    term_months = serializers.IntegerField(min_value=1, max_value=360, required=False)
    monthly_payment = serializers.DecimalField(
        max_digits=15, decimal_places=2, min_value=1, required=False
    )

    repayment_frequency = serializers.ChoiceField(
        choices=LoanApplication.REPAYMENT_FREQUENCY_CHOICES, default="monthly"
    )
    start_date = serializers.DateField(required=False)

    def validate(self, data):
        term = data.get("term_months")
        payment = data.get("monthly_payment")
        product = data.get("product")

        if not term and not payment:
            raise serializers.ValidationError(
                "Either 'term_months' or 'monthly_payment' is required."
            )
        if term and payment:
            raise serializers.ValidationError(
                "Provide either 'term_months' OR 'monthly_payment', not both."
            )

        if product.interest_type == "flat":
            if payment:
                raise serializers.ValidationError(
                    "Flat rate loans require 'term_months'. Interest is fixed upfront — monthly_payment is not applicable."
                )
        else:
            if term:
                raise serializers.ValidationError(
                    f"'{product.interest_type}' loans require 'monthly_payment'. "
                    "Use fixed payment to calculate term and total interest."
                )
        return data
