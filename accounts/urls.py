from django.urls import path

from accounts.views import (
    TokenView,
    MemberCreateView,
    SystemAdminCreateView,
    UserDetailView,
    MemberListView,
    MemberDetailView,
    ApproveMemberView,
    PasswordChangeView,
)

app_name = "accounts"

urlpatterns = [
    path("token/", TokenView.as_view(), name="token"),
    path("signup/member/", MemberCreateView.as_view(), name="member"),
    path("signup/sacco-admin/", SystemAdminCreateView.as_view(), name="sacco-admin"),
    path("<str:id>/", UserDetailView.as_view(), name="user-detail"),
    # System admin activities
    path("", MemberListView.as_view(), name="members"),
    path(
        "member/<str:member_number>/", MemberDetailView.as_view(), name="member-detail"
    ),
    path(
        "approve-member/<str:member_number>/",
        ApproveMemberView.as_view(),
        name="approve-member",
    ),
    # Password Reset
    path("password/change/", PasswordChangeView.as_view(), name="password-change"),
]
