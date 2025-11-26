from django.contrib import admin

from repayments.models import RepaymentSchedule


class RepaymentAdmin(admin.ModelAdmin):
    list_display = [
        "loan_account",
        "due_date",
        "principal_due",
        "interest_due",
        "total_due",
        "payment_type",
        "is_paid",
        "paid_amount",
        "paid_date",
    ]
    search_fields = [
        "loan_account",
        "due_date",
        "principal_due",
        "interest_due",
        "total_due",
        "payment_type",
        "is_paid",
        "paid_amount",
        "paid_date",
    ]


admin.site.register(RepaymentSchedule, RepaymentAdmin)
