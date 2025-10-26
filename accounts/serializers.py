from django.contrib.auth import get_user_model, update_session_auth_hash
from rest_framework import serializers
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from accounts.validators import (
    validate_password_digit,
    validate_password_lowercase,
    validate_password_symbol,
    validate_password_uppercase,
)
from accounts.utils import send_registration_confirmation_email

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        max_length=128,
        min_length=5,
        write_only=True,
        validators=[
            validate_password_digit,
            validate_password_uppercase,
            validate_password_symbol,
            validate_password_lowercase,
        ],
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "name",
            "phone",
            "member_number",
            "is_member",
            "is_sacco_admin",
            "is_approved",
            "is_active",
            "is_staff",
            "is_superuser",
            "created_at",
            "updated_at",
            "reference",
        )

    def create_user(self, validated_data, role_field):
        user = User.objects.create_user(**validated_data)
        setattr(user, role_field, True)
        user.is_active = True
        user.save()

        return user


class MemberSerializer(BaseUserSerializer):
    def create(self, validated_data):
        user = self.create_user(validated_data, "is_member")
        user.save()
        send_registration_confirmation_email(user)

        return user


class SystemAdminSerializer(BaseUserSerializer):
    def create(self, validated_data):
        user = self.create_user(validated_data, "is_sacco_admin")
        user.save()
        send_registration_confirmation_email(user)

        return user


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(
        max_length=128,
        min_length=5,
        write_only=True,
        validators=[
            validate_password_digit,
            validate_password_uppercase,
            validate_password_symbol,
            validate_password_lowercase,
        ],
    )

    def validate(self, attrs):
        user = self.instance  # Use self.instance instead of context
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError(
                {"old_password": "Incorrect old password"}
            )
        return attrs

    def save(self):
        user = self.instance
        password = self.validated_data.get("password")
        user.set_password(password)
        user.save()
        update_session_auth_hash(self.context["request"], user)  # Maintain session
        return user


"""
Normal login
"""


class UserLoginSerializer(serializers.Serializer):
    member_number = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
