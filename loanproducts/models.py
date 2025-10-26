from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

from accounts.abstracts import TimeStampedModel, UniversalIdModel, ReferenceModel

User = get_user_model()


class LoanProduct(UniversalIdModel, TimeStampedModel, ReferenceModel):
    INTEREST_TYPE_CHOICES = [
        ("flat", "Flat Rate (Simple on Original Principal)"),
        ("diminishing", "Diminishing Balance (Simple on Reducing Principal)"),
        ("compound", "Compound Interest"),
        ("capitalized", "Capitalized Interest"),
    ]

    INTEREST_PERIOD_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("annually", "Annually"),
    ]

    CALCULATION_SCHEDULE_CHOICES = [
        ("fixed", "Fixed Calendar (e.g., 1st of month)"),
        ("relative", "Relative to Loan Start Date"),
        ("flexible", "Custom/Flexible Schedule"),
    ]
    name = models.CharField(max_length=500, unique=True)
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
    )
    interest_type = models.CharField(max_length=50, choices=INTEREST_TYPE_CHOICES)
    interest_period = models.CharField(
        max_length=50,
        choices=INTEREST_PERIOD_CHOICES,
        default="Monthly",
        help_text="How interest is calculated",
    )
    calculation_schedule = models.CharField(
        max_length=20,
        choices=CALCULATION_SCHEDULE_CHOICES,
        default="relative",
        help_text="Defines when interest is calculated (fixed calendar, loan start date, or custom).",
    )
    compounding_frequency = models.PositiveIntegerField(
        default=1,
        blank=True,
        null=True,
        help_text="For compound/capitalized: Times per period to compound.",
    )
    description = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=3, default="KES")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Loan Product"
        verbose_name_plural = "Loan Products"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - ({self.interest_type}, {self.interest_period})"
