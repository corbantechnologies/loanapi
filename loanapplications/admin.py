from django.contrib import admin

from loanapplications.models import LoanApplication


class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "member",
        "product",
        "requested_amount",
        "term_months",
        "repayment_frequency",
        "status",
    )
    search_fields = (
        "member",
        "product",
        "requested_amount",
        "term_months",
        "repayment_frequency",
        "status",
    )


admin.site.register(LoanApplication, LoanApplicationAdmin)
