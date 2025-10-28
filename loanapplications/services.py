# loanapplications/services.py
from loanapplications.models import LoanApplication
from repayments.models import RepaymentSchedule
from loanaccounts.models import LoanAccount
from interests.projections import (
    FlatRateProjector,
    DiminishingProjector,
    CompoundProjector,
)
from datetime import date
from dateutil.relativedelta import relativedelta


def disburse_loan(application: LoanApplication):
    today = date.today()
    product = application.product

    # Create Loan Account
    account = LoanAccount.objects.create(
        member=application.member,
        product=product,
        principal=application.requested_amount,
        outstanding_balance=application.requested_amount,
        start_date=today,
        end_date=None,  # Will be set after projection
        status="Active",
    )

    # ------------------- CHOOSE PROJECTOR -------------------
    if product.interest_type == "flat":
        projection = FlatRateProjector.generate_projection(
            product=product,
            principal=application.requested_amount,
            term_months=application.term_months,
            start_date=today,
            repayment_frequency=application.repayment_frequency,
        )
    else:
        # Use monthly_payment for diminishing/compound
        projector = {
            "diminishing": DiminishingProjector,
            "compound": CompoundProjector,
        }[product.interest_type]

        projection = projector.generate_projection_fixed_payment(
            product=product,
            principal=application.requested_amount,
            monthly_payment=application.monthly_payment,
            start_date=today,
            repayment_frequency=application.repayment_frequency,
        )

    # Update end_date
    term_months = projection["term_months"]
    account.end_date = today + relativedelta(months=term_months)
    account.save()

    # Save projection
    application.projection_snapshot = projection
    application.status = "disbursed"
    application.save()

    # Create schedule
    for item in projection["schedule"]:
        RepaymentSchedule.objects.create(
            loan_account=account,
            due_date=item["due_date"],
            principal_due=item["principal_due"],
            interest_due=item["interest_due"],
            total_due=item["total_due"],
            payment_type=(
                "both"
                if item["principal_due"] > 0 and item["interest_due"] > 0
                else "interest" if item["interest_due"] > 0 else "principal"
            ),
        )

    return account
