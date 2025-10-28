from django.db import models

from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel
from loanaccounts.models import LoanAccount

class InterestLog(UniversalIdModel, TimeStampedModel, ReferenceModel):
    account = models.ForeignKey(LoanAccount, on_delete=models.CASCADE, related_name='interest_logs')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    calculation_date = models.DateField()
    interest_type = models.CharField(max_length=50)
    period_start = models.DateField()
    period_end = models.DateField()

    class Meta:
        verbose_name = "Interest Log"
        ordering = ["-calculation_date"]

    def __str__(self):
        return f"{self.amount} on {self.calculation_date} ({self.account})"
