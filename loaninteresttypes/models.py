from django.db import models

from accounts.abstracts import TimeStampedModel, UniversalIdModel, ReferenceModel


class LoanInterestType(UniversalIdModel, TimeStampedModel, ReferenceModel):
    name = models.CharField(max_length=500, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Loan Interest Type"
        verbose_name_plural = "Loan Interest Types"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
