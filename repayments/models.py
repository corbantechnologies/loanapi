from django.db import models
from accounts.abstracts import TimeStampedModel, UniversalIdModel, ReferenceModel
from loanaccounts.models import LoanAccount


class RepaymentSchedule(UniversalIdModel, TimeStampedModel, ReferenceModel):
    PAYMENT_TYPE_CHOICES = [
        ("principal", "Principal"),
        ("interest", "Interest"),
        ("both", "Principal + Interest"),
    ]

    loan_account = models.ForeignKey(
        LoanAccount,
        on_delete=models.CASCADE,
        related_name="repayment_schedule",
    )
    due_date = models.DateField()
    principal_due = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    interest_due = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_due = models.DecimalField(max_digits=15, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    is_paid = models.BooleanField(default=False)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    paid_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["due_date"]
        unique_together = ("loan_account", "due_date")

    def __str__(self):
        return f"{self.loan_account} - Due {self.due_date}: {self.total_due}"
