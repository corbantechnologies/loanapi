# interest/projections.py
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Dict, List

from loanproducts.models import LoanProduct


# ----------------------------------------------------------------------
#  COMMON HELPERS (shared by all projectors)
# ----------------------------------------------------------------------
class _BaseProjector:
    FREQUENCY_TO_DELTA = {
        "daily": relativedelta(days=1),
        "weekly": relativedelta(weeks=1),
        "biweekly": relativedelta(weeks=2),
        "monthly": relativedelta(months=1),
        "quarterly": relativedelta(months=3),
        "annually": relativedelta(years=1),
    }

    @staticmethod
    def _count_payments(term_months: int, frequency: str) -> int:
        mapping = {
            "daily": term_months * 30,
            "weekly": term_months * 4,
            "biweekly": term_months * 2,
            "monthly": term_months,
            "quarterly": max(1, term_months // 3),
            "annually": max(1, term_months // 12),
        }
        return mapping.get(frequency, 0)

    @staticmethod
    def _months_per_period(frequency: str) -> float:
        return {
            "daily": 1 / 30,
            "weekly": 1 / 4,
            "biweekly": 1 / 2,
            "monthly": 1,
            "quarterly": 3,
            "annually": 12,
        }.get(frequency, 1)

    @staticmethod
    def _time_fraction(from_date: date, to_date: date, period: str) -> Decimal:
        days = Decimal(str((to_date - from_date).days))
        denominators = {
            "daily": Decimal("365"),
            "weekly": Decimal("52") * Decimal("7"),
            "monthly": Decimal("365") / Decimal("12"),
            "annually": Decimal("365"),
        }
        return days / denominators.get(period, Decimal("1"))

    @staticmethod
    def _pmt(p: Decimal, r: Decimal, n: int) -> Decimal:
        if r == 0:
            return p / Decimal(str(n))
        return (
            p * r * (Decimal("1") + r) ** n / ((Decimal("1") + r) ** n - Decimal("1"))
        )

    @staticmethod
    def _group_by_period(schedule: List[Dict], frequency: str) -> List[Dict]:
        groups = {}
        for item in schedule:
            key = (
                item["due_date"][:7]
                if frequency in ["daily", "weekly", "biweekly", "monthly"]
                else item["due_date"][:4]
            )
            groups.setdefault(key, {"interest": 0.0, "principal": 0.0, "total": 0.0})
            groups[key]["interest"] += item["interest_due"]
            groups[key]["principal"] += item["principal_due"]
            groups[key]["total"] += item["total_due"]
        return [
            {"period": k, **{k2: round(v2, 2) for k2, v2 in v.items()}}
            for k, v in sorted(groups.items())
        ]


# ----------------------------------------------------------------------
#  1. FLAT RATE PROJECTOR
# ----------------------------------------------------------------------
class FlatRateProjector(_BaseProjector):
    @staticmethod
    def generate_projection(
        product: LoanProduct,
        principal: Decimal,
        term_months: int,
        start_date: date,
        repayment_frequency: str = "monthly",
    ) -> Dict:
        payment_delta = FlatRateProjector.FREQUENCY_TO_DELTA[repayment_frequency]
        total_payments = FlatRateProjector._count_payments(
            term_months, repayment_frequency
        )

        rate = product.interest_rate / Decimal("100")
        total_interest = (
            principal * rate * Decimal(term_months) / Decimal("12")
        ).quantize(Decimal("0.01"), ROUND_HALF_UP)
        total_repayment = principal + total_interest
        payment_amount = (total_repayment / Decimal(total_payments)).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
        interest_per_payment = (total_interest / Decimal(total_payments)).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
        principal_per_payment = payment_amount - interest_per_payment

        schedule = []
        remaining_principal = principal
        cur_date = start_date

        for i in range(total_payments):
            if i == total_payments - 1:  # last payment
                principal_due = remaining_principal
                interest_due = interest_per_payment
                total_due = principal_due + interest_due
            else:
                principal_due = principal_per_payment
                interest_due = interest_per_payment
                total_due = payment_amount

            remaining_principal = max(remaining_principal - principal_due, Decimal("0"))

            schedule.append(
                {
                    "due_date": cur_date.isoformat(),
                    "principal_due": float(principal_due),
                    "interest_due": float(interest_due),
                    "total_due": float(total_due),
                    "balance_after": float(remaining_principal),
                }
            )
            cur_date += payment_delta

        return {
            "mode": "fixed_term",
            "repayment_frequency": repayment_frequency,
            "total_payments": total_payments,
            "payment_amount": float(payment_amount),
            "term_months": term_months,
            "total_interest": float(total_interest),
            "total_repayment": float(total_repayment),
            "schedule": schedule,
            "breakdown_by_period": FlatRateProjector._group_by_period(
                schedule, repayment_frequency
            ),
        }


# ----------------------------------------------------------------------
#  2. DIMINISHING BALANCE PROJECTOR
# ----------------------------------------------------------------------
class DiminishingProjector(_BaseProjector):
    @staticmethod
    def generate_projection_fixed_payment(
        product: LoanProduct,
        principal: Decimal,
        monthly_payment: Decimal,
        start_date: date,
        repayment_frequency: str = "monthly",
        max_term_months: int = 360,
    ) -> Dict:
        payment_delta = DiminishingProjector.FREQUENCY_TO_DELTA[repayment_frequency]
        interest_delta = DiminishingProjector.FREQUENCY_TO_DELTA[
            product.interest_period
        ]

        rate = product.interest_rate / Decimal("100")
        schedule = []
        current_balance = principal
        total_interest = Decimal("0")
        cur_date = start_date
        months_elapsed = Decimal("0")

        months_per_period = Decimal(
            DiminishingProjector._months_per_period(repayment_frequency)
        )
        payment_per_period = (
            monthly_payment * months_per_period
            if repayment_frequency != "monthly"
            else monthly_payment
        ).quantize(Decimal("0.01"), ROUND_HALF_UP)

        while current_balance > Decimal("0.01") and months_elapsed < max_term_months:
            due_date = cur_date
            interest_this_period = Decimal("0")
            last_interest_calc = cur_date - payment_delta

            while last_interest_calc < due_date:
                calc_to = min(last_interest_calc + interest_delta, due_date)
                time_frac = DiminishingProjector._time_fraction(
                    last_interest_calc, calc_to, product.interest_period
                )
                period_interest = (current_balance * rate * time_frac).quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )
                interest_this_period += period_interest
                last_interest_calc = calc_to

            interest_due = min(interest_this_period, payment_per_period)
            principal_due = min(payment_per_period - interest_due, current_balance)
            total_due = interest_due + principal_due

            current_balance = (current_balance - principal_due).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )
            total_interest += interest_due

            schedule.append(
                {
                    "due_date": due_date.isoformat(),
                    "principal_due": float(principal_due),
                    "interest_due": float(interest_due),
                    "total_due": float(total_due),
                    "balance_after": float(current_balance),
                }
            )
            cur_date += payment_delta
            months_elapsed += months_per_period

        total_payments = len(schedule)
        term_months = (
            int(months_elapsed.quantize(Decimal("1"), ROUND_HALF_UP)) if schedule else 0
        )

        return {
            "mode": "fixed_payment",
            "repayment_frequency": repayment_frequency,
            "total_payments": total_payments,
            "payment_amount": float(monthly_payment),
            "term_months": term_months,
            "total_interest": float(total_interest.quantize(Decimal("0.01"))),
            "total_repayment": float(
                (principal + total_interest).quantize(Decimal("0.01"))
            ),
            "schedule": schedule,
            "breakdown_by_period": DiminishingProjector._group_by_period(
                schedule, repayment_frequency
            ),
        }


# ----------------------------------------------------------------------
#  3. COMPOUND / CAPITALIZED PROJECTOR
# ----------------------------------------------------------------------
class CompoundProjector(_BaseProjector):
    @staticmethod
    def generate_projection_fixed_payment(
        product: LoanProduct,
        principal: Decimal,
        monthly_payment: Decimal,
        start_date: date,
        repayment_frequency: str = "monthly",
        max_term_months: int = 360,
    ) -> Dict:
        payment_delta = CompoundProjector.FREQUENCY_TO_DELTA[repayment_frequency]
        interest_delta = CompoundProjector.FREQUENCY_TO_DELTA[product.interest_period]

        rate = product.interest_rate / Decimal("100")
        n = Decimal(str(product.compounding_frequency or 1))
        schedule = []
        current_balance = principal
        total_interest = Decimal("0")
        cur_date = start_date
        months_elapsed = Decimal("0")

        months_per_period = Decimal(
            CompoundProjector._months_per_period(repayment_frequency)
        )
        payment_per_period = (
            monthly_payment * months_per_period
            if repayment_frequency != "monthly"
            else monthly_payment
        ).quantize(Decimal("0.01"), ROUND_HALF_UP)

        while current_balance > Decimal("0.01") and months_elapsed < max_term_months:
            due_date = cur_date
            interest_this_period = Decimal("0")
            temp_balance = current_balance
            last_interest_calc = cur_date - payment_delta

            while last_interest_calc < due_date:
                calc_to = min(last_interest_calc + interest_delta, due_date)
                time_frac = CompoundProjector._time_fraction(
                    last_interest_calc, calc_to, product.interest_period
                )

                period_interest = temp_balance * (
                    (Decimal("1") + rate / n) ** (n * time_frac) - Decimal("1")
                )
                period_interest = period_interest.quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )

                interest_this_period += period_interest
                temp_balance += period_interest  # compound on temp only
                last_interest_calc = calc_to

            # ----- amortize -----
            interest_due = min(interest_this_period, payment_per_period)
            remaining = payment_per_period - interest_due
            principal_due = min(remaining, current_balance)
            total_due = interest_due + principal_due

            current_balance = (current_balance - principal_due).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )
            total_interest += interest_due

            # ----- capitalized adds interest AFTER payment -----
            if product.interest_type == "capitalized":
                current_balance += interest_this_period
                current_balance = current_balance.quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )

            schedule.append(
                {
                    "due_date": due_date.isoformat(),
                    "principal_due": float(principal_due),
                    "interest_due": float(interest_due),
                    "total_due": float(total_due),
                    "balance_after": float(current_balance),
                }
            )
            cur_date += payment_delta
            months_elapsed += months_per_period

        total_payments = len(schedule)
        term_months = (
            int(months_elapsed.quantize(Decimal("1"), ROUND_HALF_UP)) if schedule else 0
        )

        return {
            "mode": "fixed_payment",
            "repayment_frequency": repayment_frequency,
            "total_payments": total_payments,
            "payment_amount": float(monthly_payment),
            "term_months": term_months,
            "total_interest": float(total_interest.quantize(Decimal("0.01"))),
            "total_repayment": float(
                (principal + total_interest).quantize(Decimal("0.01"))
            ),
            "schedule": schedule,
            "breakdown_by_period": CompoundProjector._group_by_period(
                schedule, repayment_frequency
            ),
        }
