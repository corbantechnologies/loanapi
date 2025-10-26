from django.contrib import admin

from django.contrib.auth import get_user_model

User = get_user_model()


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "member_number",
        "name",
        "email",
        "phone",
        "is_member",
        "is_sacco_admin",
    )

    search_fields = ("member_number", "name", "email", "phone")


admin.site.register(User, UserAdmin)
