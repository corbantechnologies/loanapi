from django.contrib import admin

from loaninteresttypes.models import LoanInterestType


class LoanInterestTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at", "updated_at")
    search_fields = ("name",)


admin.site.register(LoanInterestType, LoanInterestTypeAdmin)
