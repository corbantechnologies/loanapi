from django.contrib import admin

from loanproducts.models import LoanProduct


class LoanProductAdmin(admin.ModelAdmin):
    list_display = ("name", "interest_rate", "interest_type", "interest_period")
    search_fields = ("name", "interest_rate", "interest_type", "interest_period")


admin.site.register(LoanProduct, LoanProductAdmin)
