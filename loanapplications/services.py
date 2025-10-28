# loanapplications/services.py
from .models import LoanApplication, RepaymentSchedule
from loanaccounts.models import LoanAccount
from interests.projections import LoanProjector
from datetime import date
from dateutil.relativedelta import relativedelta


def disburse_loan(application: LoanApplication):
    today = date.today()
    account = LoanAccount.objects.create(
        member=application.member,
        product=application.product,
        principal=application.requested_amount,
        outstanding_balance=application.requested_amount,
        start_date=today,
        end_date=today + relativedelta(months=application.term_months),
        status="Active",
    )

    # Generate & save projection
    projection = LoanProjector.generate_projection(
        product=application.product,
        principal=application.requested_amount,
        term_months=application.term_months,
        start_date=today,
        repayment_frequency=application.repayment_frequency,
    )
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
