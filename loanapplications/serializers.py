from rest_framework import serializers

from loanapplications.models import LoanApplication
from loanproducts.models import LoanProduct


# class LoanApplicationSerializer(serializers.ModelSerializer):
#     member = serializers.CharField(source="member.member_number")
#     product = serializers.SlugRelatedField(
#         slug_field="name", queryset=LoanProduct.objects.all()
#     )

#     class Meta:
#         model = LoanApplication
#         fields = (
#             "member",
#             "product",
#             "requested_amount",
#             "term_months",
#             "repayment_frequency",
#             "status",
#             "projection_snapshot",
#             "created_at",
#             "updated_at",
#             "reference",
#         )


class LoanApplicationSerializer(serializers.Serializer):
    """
    Used for input validation in projection & application creation.
    Only includes fields needed for projection.
    """

    product = serializers.SlugRelatedField(
        slug_field="name",
        queryset=LoanProduct.objects.filter(is_active=True),
        help_text="Name of the loan product",
    )
    requested_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, min_value=0
    )
    term_months = serializers.IntegerField(min_value=1, max_value=360)
    repayment_frequency = serializers.ChoiceField(
        choices=LoanApplication.REPAYMENT_FREQUENCY_CHOICES, default="monthly"
    )

    # Optional: start_date (not stored, just for projection)
    start_date = serializers.DateField(required=False)

    class Meta:
        # No model binding — this is a **projection input serializer**
        pass
