from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from cloudinary.models import CloudinaryField

from accounts.abstracts import (
    UniversalIdModel,
    MemberNumberModel,
    TimeStampedModel,
    ReferenceModel,
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, password, **extra_fields):
        user = self.model(**extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)

        return self._create_user(password, **extra_fields)

    def create_superuser(self, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_approved", True)
        extra_fields.setdefault("is_sacco_admin", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("is_approved") is not True:
            raise ValueError("Superuser must have is_approved=True.")
        if extra_fields.get("is_sacco_admin") is not True:
            raise ValueError("Superuser must have is_sacco_admin=True.")

        return self._create_user(password, **extra_fields)


class User(
    AbstractBaseUser,
    PermissionsMixin,
    UniversalIdModel,
    MemberNumberModel,
    TimeStampedModel,
    ReferenceModel,
):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=255)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    is_member = models.BooleanField(default=True)
    is_sacco_admin = models.BooleanField(default=False)

    USERNAME_FIELD = "member_number"
    REQUIRED_FIELDS = [
        "name",
        "phone",
        "email",
    ]

    objects = UserManager()

    def __str__(self):
        return f"{self.name} -{self.member_number}"
