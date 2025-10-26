import string
import secrets
import resend
import logging
from datetime import datetime
from django.template.loader import render_to_string

from loanapi.settings import DOMAIN

logger = logging.getLogger(__name__)


current_year = datetime.now().year


def generate_reference():
    characters = string.ascii_letters + string.digits
    random_string = "".join(secrets.choice(characters) for _ in range(12))
    return random_string.upper()


def generate_member_number():
    year = datetime.now().year % 100
    random_number = "".join(secrets.choice(string.digits) for _ in range(6))
    return f"M{year}{random_number}"


def send_registration_confirmation_email(user):
    """
    Resend email integration
    """
    email_body = ""
    current_year = datetime.now().year

    try:
        email_body = render_to_string(
            "registration_confirmation.html",
            {"user": user, "current_year": current_year},
        )
        params = {
            "from": "Wananchi Mali SACCO <onboarding@wananchimali.com>",
            "to": [user.email],
            "subject": "Registration Confirmation",
            "html": email_body,
        }
        response = resend.Emails.send(params)
        logger.info(f"Email sent to {user.email} with response: {response}")
        return response

    except Exception as e:
        logger.error(f"Error sending email to {user.email}: {str(e)}")
        return None


def send_member_number_email(user):
    """
    Resend email integration
    """
    email_body = ""
    current_year = datetime.now().year
    site_url = f"{DOMAIN}/login"
    password_reset_url = f"{DOMAIN}/reset-password"

    try:
        email_body = render_to_string(
            "member_number.html",
            {
                "user": user,
                "current_year": current_year,
                "site_url": site_url,
                "password_reset_url": password_reset_url,
            },
        )
        params = {
            "from": "Wananchi Mali SACCO <onboarding@wananchimali.com>",
            "to": [user.email],
            "subject": "Your Membership Number",
            "html": email_body,
        }
        response = resend.Emails.send(params)
        logger.info(f"Email sent to {user.email} with response: {response}")
        return response

    except Exception as e:
        logger.error(f"Error sending email to {user.email}: {str(e)}")
        return None
