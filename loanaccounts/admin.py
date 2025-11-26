from django.contrib import admin

from loanaccounts.models import LoanAccount


class LoanAccountAdmin(admin.ModelAdmin):
    list_display = ("member", "product", "account_number", "status")
    search_fields = ("member", "product", "account_number", "status")


admin.site.register(LoanAccount, LoanAccountAdmin)
