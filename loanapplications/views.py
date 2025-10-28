# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import date

from interests.projections import (
    FlatRateProjector,
    DiminishingProjector,
    CompoundProjector,
)
from .serializers import LoanApplicationSerializer


# --------------------------------------------------------------
#  FLAT RATE VIEW
# --------------------------------------------------------------
class FlatRateProjectionView(APIView):
    def post(self, request):
        ser = LoanApplicationSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"errors": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = ser.validated_data
        projection = FlatRateProjector.generate_projection(
            product=data["product"],
            principal=data["requested_amount"],
            term_months=data["term_months"],
            start_date=data.get("start_date", date.today()),
            repayment_frequency=data.get("repayment_frequency", "monthly"),
        )
        return Response({"projection": projection}, status=status.HTTP_200_OK)


# --------------------------------------------------------------
#  DIMINISHING BALANCE VIEW
# --------------------------------------------------------------
class DiminishingProjectionView(APIView):
    def post(self, request):
        ser = LoanApplicationSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"errors": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = ser.validated_data
        projection = DiminishingProjector.generate_projection_fixed_payment(
            product=data["product"],
            principal=data["requested_amount"],
            monthly_payment=data["monthly_payment"],
            start_date=data.get("start_date", date.today()),
            repayment_frequency=data.get("repayment_frequency", "monthly"),
        )
        return Response({"projection": projection}, status=status.HTTP_200_OK)


# --------------------------------------------------------------
#  COMPOUND / CAPITALIZED VIEW
# --------------------------------------------------------------
class CompoundProjectionView(APIView):
    def post(self, request):
        ser = LoanApplicationSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"errors": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = ser.validated_data
        projection = CompoundProjector.generate_projection_fixed_payment(
            product=data["product"],
            principal=data["requested_amount"],
            monthly_payment=data["monthly_payment"],
            start_date=data.get("start_date", date.today()),
            repayment_frequency=data.get("repayment_frequency", "monthly"),
        )
        return Response({"projection": projection}, status=status.HTTP_200_OK)
