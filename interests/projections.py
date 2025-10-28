# interest/projections.py
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from dateutil.relativedelta import relativedelta


class LoanProjector:
    FREQUENCY_TO_DELTA = {
        "daily": relativedelta(days=1),
        "weekly": relativedelta(weeks=1),
        "biweekly": relativedelta(weeks=2),
        "monthly": relativedelta(months=1),
        "quarterly": relativedelta(months=3),
        "annually": relativedelta(years=1),
    }

    @staticmethod
    def generate_projection(
        product,
        principal: Decimal,
        term_months: int,
        start_date: date,
        repayment_frequency: str = "monthly",
    ) -> dict:
        if repayment_frequency not in LoanProjector.FREQUENCY_TO_DELTA:
            raise ValueError("Invalid repayment frequency")

        payment_delta = LoanProjector.FREQUENCY_TO_DELTA[repayment_frequency]
        interest_delta = LoanProjector.FREQUENCY_TO_DELTA[product.interest_period]

        total_payments = LoanProjector._count_payments(term_months, repayment_frequency)
        if total_payments == 0:
            return {"error": "Invalid term or frequency"}

        schedule = []
        current_balance = principal
        total_interest = Decimal("0")
        rate = product.interest_rate / Decimal("100")  # ← Safe: 100 → Decimal
        interest_accrued = Decimal("0")
        last_interest_calc = start_date
        cur_payment_date = start_date

        # EMI for flat/diminishing
        if product.interest_type in ["flat", "diminishing"]:
            monthly_rate = rate / Decimal("12")  # ← FIX: Use Decimal('12')
            emi = LoanProjector._pmt(principal, monthly_rate, term_months)
            payment_per_period = emi * Decimal(
                str(LoanProjector._months_per_period(repayment_frequency))
            )  # ← Safe
        else:
            payment_per_period = None

        for i in range(total_payments):
            due_date = cur_payment_date

            # Accrue interest
            interest_this_period = Decimal("0")
            while last_interest_calc < due_date:
                calc_to = min(last_interest_calc + interest_delta, due_date)
                time_frac = LoanProjector._time_fraction(
                    last_interest_calc, calc_to, product.interest_period
                )

                if product.interest_type == "flat":
                    period_interest = principal * rate * time_frac
                elif product.interest_type == "diminishing":
                    period_interest = current_balance * rate * time_frac
                elif product.interest_type in ["compound", "capitalized"]:
                    n = Decimal(str(product.compounding_frequency or 1))
                    period_interest = current_balance * (
                        (Decimal("1") + rate / n) ** (n * time_frac) - Decimal("1")
                    )
                    if product.interest_type == "capitalized":
                        current_balance += period_interest
                else:
                    period_interest = Decimal("0")

                interest_accrued += period_interest
                interest_this_period += period_interest
                last_interest_calc = calc_to

            # Apply payment
            if product.interest_type in ["flat", "diminishing"]:
                total_due = payment_per_period
                interest_due = min(interest_accrued, total_due)
                principal_due = total_due - interest_due
                if i == total_payments - 1:
                    principal_due = current_balance
                    total_due = principal_due + interest_accrued
                current_balance = max(current_balance - principal_due, Decimal("0"))
                interest_accrued = max(interest_accrued - interest_due, Decimal("0"))
            else:
                interest_due = interest_this_period
                principal_due = Decimal("0")
                total_due = interest_due

            total_interest += interest_due

            schedule.append(
                {
                    "due_date": due_date.isoformat(),
                    "principal_due": float(
                        principal_due.quantize(Decimal("0.01"), ROUND_HALF_UP)
                    ),
                    "interest_due": float(
                        interest_due.quantize(Decimal("0.01"), ROUND_HALF_UP)
                    ),
                    "total_due": float(
                        total_due.quantize(Decimal("0.01"), ROUND_HALF_UP)
                    ),
                    "balance_after": float(
                        current_balance.quantize(Decimal("0.01"), ROUND_HALF_UP)
                    ),
                }
            )

            cur_payment_date += payment_delta

        return {
            "repayment_frequency": repayment_frequency,
            "total_payments": total_payments,
            "payment_amount": (
                float(payment_per_period.quantize(Decimal("0.01")))
                if payment_per_period
                else None
            ),
            "total_interest": float(total_interest.quantize(Decimal("0.01"))),
            "total_repayment": float(
                (principal + total_interest).quantize(Decimal("0.01"))
            ),
            "schedule": schedule,
            "breakdown_by_period": LoanProjector._group_by_period(
                schedule, repayment_frequency
            ),
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
        days = Decimal(str((to_date - from_date).days))  # ← Safe
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
    def _group_by_period(schedule: list, frequency: str) -> list:
        groups = {}
        for item in schedule:
            key = (
                item["due_date"][:7]
                if frequency in ["daily", "weekly", "biweekly", "monthly"]
                else item["due_date"][:4]
            )
            groups.setdefault(key, {"interest": 0, "principal": 0, "total": 0})
            groups[key]["interest"] += item["interest_due"]
            groups[key]["principal"] += item["principal_due"]
            groups[key]["total"] += item["total_due"]
        return [{"period": k, **v} for k, v in sorted(groups.items())]
