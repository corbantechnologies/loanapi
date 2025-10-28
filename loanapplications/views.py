# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from loanapplications.serializers import LoanApplicationSerializer
from loanapplications.services import disburse_loan

from datetime import date
from interests.projections import (
    FlatRateProjector,
    DiminishingProjector,
    CompoundProjector,
)


class LoanApplicationCreateView(APIView):
    def post(self, request):
        serializer = LoanApplicationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Save the application
        application = serializer.save(status="approved")  # or whatever

        # 2. DISBURSE THE LOAN → This generates correct projection
        try:
            loan_account = disburse_loan(application)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Return the correct projection
        return Response(
            {
                "message": "Loan disbursed successfully",
                "loan_account_id": loan_account.id,
                "projection": application.projection_snapshot,
            },
            status=status.HTTP_201_CREATED,
        )


# views.py
class LoanProjectionPreviewView(APIView):
    def post(self, request):
        ser = LoanApplicationSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"errors": ser.errors}, status=400)

        data = ser.validated_data
        product = data["product"]

        if product.interest_type == "flat":
            proj = FlatRateProjector.generate_projection(
                product=product,
                principal=data["requested_amount"],
                term_months=data["term_months"],
                start_date=data.get("start_date", date.today()),
                repayment_frequency=data.get("repayment_frequency", "monthly"),
            )
        else:
            projector = {
                "diminishing": DiminishingProjector,
                "compound": CompoundProjector,
            }
            proj = projector[product.interest_type].generate_projection_fixed_payment(
                product=product,
                principal=data["requested_amount"],
                monthly_payment=data["monthly_payment"],
                start_date=data.get("start_date", date.today()),
                repayment_frequency=data.get("repayment_frequency", "monthly"),
            )

        return Response({"projection": proj})
