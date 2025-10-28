# loans.py
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Dict, List


# -------------------------------------------------------------------------
# 1. REDUCING (DIMINISHING) BALANCE
# -------------------------------------------------------------------------
def reducing_balance(
    principal: Decimal,
    annual_rate: Decimal,  # e.g. 10.00
    payment_per_month: Decimal,  # fixed amount the borrower pays each month
    start_date: date = date.today(),
    repayment_frequency: str = "monthly",
    max_months: int = 360,
) -> Dict:
    """
    Returns:
        {
            "term_months": int,
            "total_interest": float,
            "total_repayment": float,
            "schedule": List[dict]
        }
    """
    # ----- helpers -------------------------------------------------------
    DELTA = {
        "daily": relativedelta(days=1),
        "weekly": relativedelta(weeks=1),
        "biweekly": relativedelta(weeks=2),
        "monthly": relativedelta(months=1),
        "quarterly": relativedelta(months=3),
        "annually": relativedelta(years=1),
    }
    MONTHS_IN_PERIOD = {
        "daily": Decimal("1") / 30,
        "weekly": Decimal("1") / 4,
        "biweekly": Decimal("0.5"),
        "monthly": Decimal("1"),
        "quarterly": Decimal("3"),
        "annually": Decimal("12"),
    }

    if repayment_frequency not in DELTA:
        raise ValueError(f"Unsupported frequency: {repayment_frequency}")

    payment_delta = DELTA[repayment_frequency]
    months_per_period = MONTHS_IN_PERIOD[repayment_frequency]

    # ----- initialise ----------------------------------------------------
    rate = annual_rate / Decimal("100")  # annual → decimal
    balance = principal
    total_interest = Decimal("0")
    cur_date = start_date
    months_elapsed = Decimal("0")
    schedule: List[dict] = []

    payment_this_period = (payment_per_month * months_per_period).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )

    # ----- main loop -----------------------------------------------------
    while balance > Decimal("0.01") and months_elapsed < max_months:
        due = cur_date

        # ---- interest for the *whole* period (daily steps) -------------
        interest_this_period = Decimal("0")
        calc_from = due - payment_delta

        while calc_from < due:
            calc_to = min(calc_from + relativedelta(days=1), due)
            days = (calc_to - calc_from).days
            time_frac = Decimal(days) / Decimal("365")
            period_int = (balance * rate * time_frac).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )
            interest_this_period += period_int
            calc_from = calc_to

        # ---- apply payment (interest first) ---------------------------
        interest_due = min(interest_this_period, payment_this_period)
        principal_due = min(payment_this_period - interest_due, balance)
        total_due = interest_due + principal_due

        balance = (balance - principal_due).quantize(Decimal("0.01"), ROUND_HALF_UP)
        total_interest += interest_due

        schedule.append(
            {
                "due_date": due.isoformat(),
                "principal_due": float(principal_due),
                "interest_due": float(interest_due),
                "total_due": float(total_due),
                "balance_after": float(balance),
            }
        )

        cur_date += payment_delta
        months_elapsed += months_per_period

    # ----- final totals --------------------------------------------------
    term_months = int(months_elapsed.quantize(Decimal("1"), ROUND_HALF_UP))
    return {
        "term_months": term_months,
        "total_interest": float(total_interest.quantize(Decimal("0.01"))),
        "total_repayment": float(
            (principal + total_interest).quantize(Decimal("0.01"))
        ),
        "schedule": schedule,
    }


# -------------------------------------------------------------------------
# 2. COMPOUND INTEREST (interest added to balance before payment)
# -------------------------------------------------------------------------
def compound_balance(
    principal: Decimal,
    annual_rate: Decimal,
    payment_per_month: Decimal,
    start_date: date = date.today(),
    repayment_frequency: str = "monthly",
    compounding_times_per_year: int = 12,  # 12 = monthly, 1 = annually, …
    max_months: int = 360,
) -> Dict:
    """
    Same return format as `reducing_balance`.
    """
    DELTA = {
        "daily": relativedelta(days=1),
        "weekly": relativedelta(weeks=1),
        "biweekly": relativedelta(weeks=2),
        "monthly": relativedelta(months=1),
        "quarterly": relativedelta(months=3),
        "annually": relativedelta(years=1),
    }
    MONTHS_IN_PERIOD = {
        "daily": Decimal("1") / 30,
        "weekly": Decimal("1") / 4,
        "biweekly": Decimal("0.5"),
        "monthly": Decimal("1"),
        "quarterly": Decimal("3"),
        "annually": Decimal("12"),
    }

    if repayment_frequency not in DELTA:
        raise ValueError(f"Unsupported frequency: {repayment_frequency}")

    payment_delta = DELTA[repayment_frequency]
    months_per_period = MONTHS_IN_PERIOD[repayment_frequency]

    rate = annual_rate / Decimal("100")
    n = Decimal(str(compounding_times_per_year))

    balance = principal
    total_interest = Decimal("0")
    cur_date = start_date
    months_elapsed = Decimal("0")
    schedule: List[dict] = []

    payment_this_period = (payment_per_month * months_per_period).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )

    while balance > Decimal("0.01") and months_elapsed < max_months:
        due = cur_date

        # ---- compound interest for the period (daily steps) ----------
        interest_this_period = Decimal("0")
        calc_from = due - payment_delta

        while calc_from < due:
            calc_to = min(calc_from + relativedelta(days=1), due)
            days = (calc_to - calc_from).days
            time_frac = Decimal(days) / Decimal("365")
            # compound formula for a tiny slice
            period_int = balance * (
                (Decimal("1") + rate / n) ** (n * time_frac) - Decimal("1")
            )
            period_int = period_int.quantize(Decimal("0.01"), ROUND_HALF_UP)

            interest_this_period += period_int
            balance += period_int  # **compound**
            calc_from = calc_to

        # ---- apply payment (interest first) -------------------------
        interest_due = min(interest_this_period, payment_this_period)
        principal_due = min(payment_this_period - interest_due, balance)
        total_due = interest_due + principal_due

        balance = (balance - principal_due).quantize(Decimal("0.01"), ROUND_HALF_UP)
        total_interest += interest_due

        schedule.append(
            {
                "due_date": due.isoformat(),
                "principal_due": float(principal_due),
                "interest_due": float(interest_due),
                "total_due": float(total_due),
                "balance_after": float(balance),
            }
        )

        cur_date += payment_delta
        months_elapsed += months_per_period

    term_months = int(months_elapsed.quantize(Decimal("1"), ROUND_HALF_UP))
    return {
        "term_months": term_months,
        "total_interest": float(total_interest.quantize(Decimal("0.01"))),
        "total_repayment": float(
            (principal + total_interest).quantize(Decimal("0.01"))
        ),
        "schedule": schedule,
    }


# -------------------------------------------------------------------------
# 3. INTERACTIVE TEST (run the file directly)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n=== Simple Loan Calculator ===\n")
    print("1 – Reducing (Diminishing) Balance")
    print("2 – Compound Interest")
    choice = input("\nSelect (1 or 2): ").strip()

    principal = Decimal(input("\nPrincipal amount: ").strip())
    annual_rate = Decimal(input("Annual interest rate (e.g. 10.00): ").strip())
    payment = Decimal(input("Fixed payment per month: ").strip())
    freq = (
        input("Repayment frequency (monthly, weekly, …) [default: monthly]: ").strip()
        or "monthly"
    )

    if choice == "1":
        res = reducing_balance(
            principal, annual_rate, payment, repayment_frequency=freq
        )
        print("\n--- REDUCING BALANCE ---")
    elif choice == "2":
        comp_times = int(
            input(
                "Compounding times per year (12 = monthly, 1 = yearly) [default 12]: "
            ).strip()
            or "12"
        )
        res = compound_balance(
            principal,
            annual_rate,
            payment,
            repayment_frequency=freq,
            compounding_times_per_year=comp_times,
        )
        print("\n--- COMPOUND INTEREST ---")
    else:
        raise SystemExit("Invalid choice")

    print(f"Term (months)      : {res['term_months']}")
    print(f"Total interest     : {res['total_interest']:,}")
    print(f"Total repayment    : {res['total_repayment']:,}")
    print(f"Payments made      : {len(res['schedule'])}\n")

    print("Schedule (first 10 + last 2):")
    for i, line in enumerate(res["schedule"][:10]):
        print(f"{i+1:2}: {line}")
    if len(res["schedule"]) > 12:
        print(" …")
        for line in res["schedule"][-2:]:
            print(line)
