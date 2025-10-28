from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from loanaccounts.models import LoanAccount
from interests.models import InterestLog


class InterestCalculator:
    """
    - generate interest of the loan product according to its type
    - generate monthly interest to be paid
    - generate annual interest to be paid
    - generate total interest to be paid
    - generate total amount to be repaid back including interest
    - store interest logs
    - update last interest calculation
    """

    @staticmethod
    def calculate_interest(account: LoanAccount, current_date: date = None) -> Decimal:
        if current_date is None:
            current_date = timezone.now().date()

        product = account.product
        last_calc = account.last_interest_calulation or account.start_date

        # skip if already calculated today or not due
        if last_calc >= current_date:
            return Decimal(0.00)

        # Determine period
        from_date, to_date = InterestCalculator._get_calculation_period(
            account, current_date
        )
        if from_date >= to_date:
            return Decimal(0.00)

        # Calculate interest
        interest = InterestCalculator._calculate_by_type(account, from_date, to_date)

        # Log and update account
        InterestLog.objects.create(
            account=account,
            amount=interest,
            calculation_date=to_date,
            interest_type=product.interest_type,
            period_start=from_date,
            period_end=to_date,
        )

        # Update balance and last calc
        account.outstanding_balance += interest
        account.last_interest_calculation = to_date
        account.save(update_fields=["outstanding_balance", "last_interest_calculation"])

        return interest

    # ----------------------------------------------
    # Core Calculation Logic
    # ----------------------------------------------

    @staticmethod
    def _calculate_by_type(
        account: LoanAccount, from_date: date, to_date: date
    ) -> Decimal:
        product = account.product
        rate = product.interest_rate / Decimal(100)
        time_fraction = InterestCalculator._get_time_fraction(
            from_date, to_date, product.interest_period
        )

        if product.interest_type == "flat":
            return (account.principal * rate * time_fraction).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )

        elif product.interest_type == "diminishing":
            # Use average balance over period (or current_balance at start)
            balance = account._get_balance_at_date(
                from_date
            )  # Custom method or from repayment history
            return (balance * rate * time_fraction).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )

        elif product.interest_type == "compound":
            n = product.compounding_frequency or 1
            effective_principal = account.principal
            return (
                effective_principal * ((1 + rate / n) ** (n * time_fraction) - 1)
            ).quantize(Decimal("0.01"), ROUND_HALF_UP)

        elif product.interest_type == "capitalized":
            interest = InterestCalculator._calculate_by_type(
                account, from_date, to_date
            )  # Recursive base
            account.principal += interest
            account.save(update_fields=["principal"])
            return interest

        raise ValueError(f"Unknown interest type: {product.interest_type}")

    # ——————————————————————————————————————
    # Period & Schedule Logic
    # ——————————————————————————————————————

    @staticmethod
    def _get_calculation_period(
        account: LoanAccount, current_date: date
    ) -> tuple[date, date]:
        product = account.product
        last_calc = account.last_interest_calculation or account.start_date

        if product.calculation_schedule == "fixed":
            return InterestCalculator._fixed_calendar_period(
                product, current_date, last_calc
            )
        elif product.calculation_schedule == "relative":
            return InterestCalculator._relative_period(product, last_calc, current_date)
        elif product.calculation_schedule == "flexible":
            return last_calc, current_date
        else:
            return last_calc, current_date

    @staticmethod
    def _fixed_calendar_period(product, current_date, last_calc):
        if product.interest_period == "monthly":
            target = current_date.replace(day=1)
            if current_date.day == 1:
                from_date = (target - relativedelta(months=1)).replace(day=1)
                to_date = target
            else:
                from_date = target
                to_date = target + relativedelta(months=1)
                to_date = min(to_date, current_date)
        elif product.interest_period == "annually":
            target = current_date.replace(month=1, day=1)
            if current_date.month == 1 and current_date.day == 1:
                from_date = target - relativedelta(years=1)
                to_date = target
            else:
                from_date = target
                to_date = target + relativedelta(years=1)
                to_date = min(to_date, current_date)
        else:
            from_date = last_calc
            to_date = current_date
        return from_date, to_date

    @staticmethod
    def _relative_period(product, last_calc, current_date):
        delta_map = {
            "daily": relativedelta(days=1),
            "weekly": relativedelta(weeks=1),
            "monthly": relativedelta(months=1),
            "annually": relativedelta(years=1),
        }
        delta = delta_map[product.interest_period]
        expected_next = last_calc + delta
        if current_date >= expected_next:
            return last_calc, expected_next
        else:
            return last_calc, current_date

    @staticmethod
    def _get_time_fraction(from_date: date, to_date: date, period: str) -> Decimal:
        days = (to_date - from_date).days
        if period == "daily":
            return Decimal(days) / 365
        elif period == "weekly":
            return Decimal(days) / (52 * 7)
        elif period == "monthly":
            return Decimal(days) / (365 / 12)
        elif period == "annually":
            return Decimal(days) / 365
        return Decimal("0")

    # ——————————————————————————————————————
    # Projection Helpers (Monthly, Annual, Total)
    # ——————————————————————————————————————

    @staticmethod
    def monthly_interest_projection(account: LoanAccount) -> Decimal:
        """Estimated interest per month (for UI/schedules)"""
        product = account.product
        rate = product.interest_rate / Decimal("100")
        monthly_rate = rate / 12

        if product.interest_type == "flat":
            return (account.principal * monthly_rate).quantize(Decimal("0.01"))
        elif product.interest_type == "diminishing":
            return (account.outstanding_balance * monthly_rate).quantize(
                Decimal("0.01")
            )
        elif product.interest_type in ["compound", "capitalized"]:
            n = product.compounding_frequency or 12
            effective_rate = (1 + rate / n) ** (n / 12) - 1
            return (account.principal * effective_rate).quantize(Decimal("0.01"))
        return Decimal("0.00")

    @staticmethod
    def total_interest_projection(account: LoanAccount) -> Decimal:
        """Total interest over full loan term"""
        months = (
            (account.end_date.year - account.start_date.year) * 12
            + account.end_date.month
            - account.start_date.month
        )
        return InterestCalculator.monthly_interest_projection(account) * months

    @staticmethod
    def total_repayment_amount(account: LoanAccount) -> Decimal:
        """Principal + Total Interest"""
        return account.principal + InterestCalculator.total_interest_projection(account)
