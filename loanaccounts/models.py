from django.db import models
from django.contrib.auth import get_user_model

from loanproducts.models import LoanProduct
from loanaccounts.utils import generate_loan_account_number
from accounts.abstracts import TimeStampedModel, UniversalIdModel, ReferenceModel

User = get_user_model()


class LoanAccount(UniversalIdModel, TimeStampedModel, ReferenceModel):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Closed", "Closed"),
        ("Defaulted", "Defaulted"),
    ]

    member = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="loan_accounts"
    )
    product = models.ForeignKey(
        LoanProduct, on_delete=models.CASCADE, related_name="loans"
    )
    account_number = models.CharField(
        max_length=20, unique=True, default=generate_loan_account_number
    )
    principal = models.DecimalField(max_digits=15, decimal_places=2)
    outstanding_balance = models.DecimalField(max_digits=15, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    last_interest_calulation = models.DateField(null=True, blank=True)
    status = models.CharField(choices=STATUS_CHOICES, default="Active", max_length=20)

    class Meta:
        verbose_name = "Loan Account"
        verbose_name_plural = "Loan Accounts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.member} - {self.product}"
