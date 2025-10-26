import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from accounts.serializers import (
    BaseUserSerializer,
    MemberSerializer,
    UserLoginSerializer,
    SystemAdminSerializer,
    PasswordChangeSerializer,
)
from accounts.utils import send_member_number_email
from accounts.permissions import IsSystemAdmin

User = get_user_model()


"""
Authentication
"""


class TokenView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            member_number = serializer.validated_data["member_number"]
            password = serializer.validated_data["password"]

            user = authenticate(member_number=member_number, password=password)

            if user:
                if user.is_approved:
                    token, created = Token.objects.get_or_create(user=user)
                    user_details = {
                        "id": user.id,
                        "email": user.email,
                        "name": user.name,
                        "member_number": user.member_number,
                        "reference": user.reference,
                        "is_member": user.is_member,
                        "is_sacco_admin": user.is_sacco_admin,
                        "is_active": user.is_active,
                        "is_staff": user.is_staff,
                        "is_superuser": user.is_superuser,
                        "is_approved": user.is_approved,
                        "last_login": user.last_login,
                        "token": token.key,
                    }
                    return Response(user_details, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {"detail": ("User account is not verified.")},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {"detail": ("Unable to log in with provided credentials.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""
Create and Detail Views
"""


class MemberCreateView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = MemberSerializer
    queryset = User.objects.all()


class SystemAdminCreateView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = SystemAdminSerializer
    queryset = User.objects.all()


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BaseUserSerializer
    queryset = User.objects.all()
    lookup_field = "id"

    def get_queryset(self):
        return super().get_queryset().filter(id=self.request.user.id)


"""
System admin views
- Approve new members
- View list of members
"""


class MemberListView(generics.ListAPIView):
    """
    Fetch the list of members
    """

    permission_classes = (IsSystemAdmin,)
    serializer_class = BaseUserSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        """
        Fetch is_member and is_sacco_admin field
        Users with is_sacco_admin are also members
        """
        return super().get_queryset().filter(
            is_member=True
        ) | super().get_queryset().filter(is_sacco_admin=True)


class MemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View, update and delete a member
    """

    permission_classes = (IsSystemAdmin,)
    serializer_class = BaseUserSerializer
    queryset = User.objects.all()
    lookup_field = "member_number"


class ApproveMemberView(generics.RetrieveUpdateAPIView):
    """
    Approve a new member after self registration.
    Email is compulsory
    """

    permission_classes = (IsSystemAdmin,)
    serializer_class = BaseUserSerializer
    queryset = User.objects.all()
    lookup_field = "member_number"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Validate that user is not already approved
        if instance.is_approved:
            return Response(
                {"detail": "User is already approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Approve user and assign member number
        instance.is_approved = True
        instance.is_active = True
        instance.save()

        # Send member number email
        try:
            send_member_number_email(user=instance)
        except Exception as e:
            # Log the error (use your preferred logging mechanism)
            print(f"Failed to send email to {instance.email}: {str(e)}")
            return Response(
                {"detail": "User approved, but failed to send email."},
                status=status.HTTP_200_OK,
            )

        serializer = self.get_serializer(instance)
        return Response(
            {"detail": "User approved successfully.", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

"""
Passwords
"""

class PasswordChangeView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PasswordChangeSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {"detail": "Password changed successfully"}, status=status.HTTP_200_OK
        )
