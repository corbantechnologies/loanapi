# loanapplications/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from decimal import Decimal
from datetime import date

from interests.projections import LoanProjector
from loanproducts.models import LoanProduct
from loanapplications.serializers import LoanApplicationSerializer


class LoanProjectionView(APIView):
    """
    POST: Generate full loan projection (schedule, totals, breakdowns)
    Input is validated using LoanApplicationSerializer (only relevant fields)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Use serializer to validate input
        serializer = LoanApplicationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        try:
            # 2. Extract data
            product = validated_data["product"]
            principal = Decimal(validated_data["requested_amount"])
            term_months = validated_data["term_months"]
            repayment_frequency = validated_data.get("repayment_frequency", "monthly")
            start_date = date.fromisoformat(
                request.data.get("start_date", str(date.today()))
            )

            # 3. Generate projection
            projection = LoanProjector.generate_projection(
                product=product,
                principal=principal,
                term_months=term_months,
                start_date=start_date,
                repayment_frequency=repayment_frequency,
            )

            # 4. Return rich response
            return Response(
                {
                    "projection": projection,
                    "summary": {
                        "total_interest": projection["total_interest"],
                        "total_repayment": projection["total_repayment"],
                        "payment_frequency": projection["repayment_frequency"],
                        "total_payments": projection["total_payments"],
                    },
                },
                status=status.HTTP_200_OK,
            )

        except LoanProduct.DoesNotExist:
            return Response(
                {"error": "Loan product not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
