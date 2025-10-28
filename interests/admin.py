from django.contrib import admin

from interests.models import InterestLog


class InterestLogAdmin(admin.ModelAdmin):
    list_display = (
        "account",
        "amount",
        "calculation_date",
        "interest_type",
        "period_start",
        "period_end",
    )
    search_fields = (
        "account",
        "amount",
        "calculation_date",
        "interest_type",
        "period_start",
        "period_end",
    )


admin.site.register(InterestLog)
