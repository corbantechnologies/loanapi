from django.db import models
from accounts.abstracts import TimeStampedModel, UniversalIdModel, ReferenceModel
from django.contrib.auth import get_user_model

from loanproducts.models import LoanProduct

User = get_user_model()


class LoanApplication(UniversalIdModel, TimeStampedModel, ReferenceModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("disbursed", "Disbursed"),
    ]

    REPAYMENT_FREQUENCY_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("biweekly", "Biweekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("annually", "Annually"),
    ]

    member = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="loan_applications"
    )
    product = models.ForeignKey(LoanProduct, on_delete=models.PROTECT)
    requested_amount = models.DecimalField(max_digits=15, decimal_places=2)
    term_months = models.PositiveIntegerField()
    repayment_frequency = models.CharField(
        max_length=20,
        choices=REPAYMENT_FREQUENCY_CHOICES,
        default="monthly",
        help_text="How often borrower makes payments",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    projection_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text="Exact projection shown to borrower at application time",
    )

    class Meta:
        ordering = ["-created_at"]
        unique_together = (
            "member",
            "product",
            "requested_amount",
            "term_months",
            "repayment_frequency",
        )

    def __str__(self):
        return f"{self.member} - {self.product.name} ({self.requested_amount})"
