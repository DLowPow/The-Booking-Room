"""
Banking System - Bank loans and Loan Shark
Bank: Lower interest, safe, weekly auto-repayments from profits
Loan Shark: Higher interest, penalties for missed payments
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class LoanType(Enum):
    BANK = "Bank Loan"
    LOAN_SHARK = "Loan Shark"


class LoanStatus(Enum):
    ACTIVE = "Active"
    PAID_OFF = "Paid Off"
    DEFAULTED = "Defaulted"
    PENALTY = "Penalty Applied"


# Bank loan tiers
BANK_LOAN_OPTIONS = {
    "small": {"amount": 5000, "interest_rate": 0.05, "weeks": 12, "label": "Small Loan"},
    "medium": {"amount": 15000, "interest_rate": 0.08, "weeks": 20, "label": "Medium Loan"},
    "large": {"amount": 30000, "interest_rate": 0.12, "weeks": 30, "label": "Large Loan"},
    "major": {"amount": 50000, "interest_rate": 0.15, "weeks": 40, "label": "Major Loan"},
    "massive": {"amount": 100000, "interest_rate": 0.20, "weeks": 52, "label": "Massive Loan"},
}

# Loan shark options - higher amounts, much higher interest
SHARK_LOAN_OPTIONS = {
    "quick_cash": {"amount": 3000, "interest_rate": 0.15, "weeks": 8, "label": "Quick Cash"},
    "street_money": {"amount": 10000, "interest_rate": 0.25, "weeks": 12, "label": "Street Money"},
    "big_deal": {"amount": 25000, "interest_rate": 0.35, "weeks": 16, "label": "Big Deal"},
    "dangerous": {"amount": 50000, "interest_rate": 0.50, "weeks": 20, "label": "Dangerous Money"},
    "death_wish": {"amount": 100000, "interest_rate": 0.75, "weeks": 26, "label": "Death Wish"},
}

SHARK_PHONE_NUMBER = "555-SHARK"
SHARK_MISSED_PENALTY_MULTIPLIER = 2.0


@dataclass
class Loan:
    id: str
    loan_type: LoanType
    principal: int
    interest_rate: float
    total_owed: int
    weekly_payment: int
    weeks_total: int
    weeks_remaining: int
    amount_paid: int = 0
    status: LoanStatus = LoanStatus.ACTIVE
    missed_payments: int = 0
    penalty_active: bool = False
    date_taken: str = ""

    def make_payment(self, amount: int) -> Dict:
        """Make a payment on the loan. Returns payment result."""
        if self.status != LoanStatus.ACTIVE:
            return {"success": False, "message": "Loan is not active"}

        actual_payment = min(amount, self.total_owed - self.amount_paid)
        self.amount_paid += actual_payment
        self.weeks_remaining -= 1

        remaining = self.total_owed - self.amount_paid

        if remaining <= 0:
            self.status = LoanStatus.PAID_OFF
            return {
                "success": True, "payment": actual_payment,
                "remaining": 0, "paid_off": True,
                "message": "🎉 Loan fully paid off!",
            }

        return {
            "success": True, "payment": actual_payment,
            "remaining": remaining, "paid_off": False,
            "message": f"Payment of ${actual_payment:,} made. ${remaining:,} remaining.",
        }

    def miss_payment(self) -> Dict:
        """Handle a missed payment"""
        self.missed_payments += 1
        self.weeks_remaining -= 1

        result = {"missed": True, "missed_total": self.missed_payments}

        if self.loan_type == LoanType.LOAN_SHARK:
            # Loan shark doubles next payment
            self.penalty_active = True
            penalty_amount = self.weekly_payment
            self.total_owed += penalty_amount
            result["penalty"] = penalty_amount
            result["message"] = f"⚠️ MISSED PAYMENT! Loan Shark adds ${penalty_amount:,} penalty. Next week you owe DOUBLE!"
        else:
            # Bank adds small late fee
            late_fee = int(self.weekly_payment * 0.1)
            self.total_owed += late_fee
            result["penalty"] = late_fee
            result["message"] = f"⚠️ Missed payment. Late fee: ${late_fee:,}"

        if self.missed_payments >= 3 and self.loan_type == LoanType.LOAN_SHARK:
            self.status = LoanStatus.DEFAULTED
            result["defaulted"] = True
            result["message"] = "🚨 DEFAULTED on Loan Shark! Serious consequences!"

        return result

    def get_next_payment(self) -> int:
        """Get the amount due next week"""
        if self.penalty_active and self.loan_type == LoanType.LOAN_SHARK:
            return int(self.weekly_payment * SHARK_MISSED_PENALTY_MULTIPLIER)
        return self.weekly_payment

    def get_remaining_balance(self) -> int:
        return max(0, self.total_owed - self.amount_paid)

    def get_progress_percentage(self) -> float:
        if self.total_owed <= 0:
            return 100.0
        return min(100.0, (self.amount_paid / self.total_owed) * 100)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "loan_type": self.loan_type.value,
            "principal": self.principal, "interest_rate": self.interest_rate,
            "total_owed": self.total_owed, "weekly_payment": self.weekly_payment,
            "weeks_total": self.weeks_total, "weeks_remaining": self.weeks_remaining,
            "amount_paid": self.amount_paid, "status": self.status.value,
            "missed_payments": self.missed_payments,
            "penalty_active": self.penalty_active,
            "date_taken": self.date_taken,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Loan":
        return cls(
            id=data["id"], loan_type=LoanType(data["loan_type"]),
            principal=data["principal"], interest_rate=data["interest_rate"],
            total_owed=data["total_owed"], weekly_payment=data["weekly_payment"],
            weeks_total=data["weeks_total"], weeks_remaining=data["weeks_remaining"],
            amount_paid=data.get("amount_paid", 0),
            status=LoanStatus(data.get("status", "Active")),
            missed_payments=data.get("missed_payments", 0),
            penalty_active=data.get("penalty_active", False),
            date_taken=data.get("date_taken", ""),
        )


class BankingManager:
    def __init__(self):
        self.active_loans: List[Loan] = []
        self.loan_history: List[Loan] = []
        self.next_id: int = 1
        self.total_interest_paid: int = 0
        self.total_borrowed: int = 0
        self.credit_score: int = 500  # 300-850 range

    def can_take_loan(self, loan_type: LoanType) -> tuple:
        """Check if player can take a new loan"""
        active_of_type = [l for l in self.active_loans if l.loan_type == loan_type and l.status == LoanStatus.ACTIVE]

        if loan_type == LoanType.BANK:
            if len(active_of_type) >= 2:
                return False, "Maximum 2 bank loans at a time"
            if self.credit_score < 400:
                return False, "Credit score too low for bank loans"
        elif loan_type == LoanType.LOAN_SHARK:
            if len(active_of_type) >= 3:
                return False, "Even the Loan Shark has limits... 3 max"
            # Loan shark doesn't check credit

        # Check for defaults
        defaulted = [l for l in self.active_loans if l.status == LoanStatus.DEFAULTED]
        if defaulted and loan_type == LoanType.BANK:
            return False, "Cannot get bank loans while in default"

        return True, "Approved"

    def take_loan(self, loan_type: LoanType, option_key: str, date_str: str = "") -> Optional[Loan]:
        """Take out a new loan"""
        if loan_type == LoanType.BANK:
            options = BANK_LOAN_OPTIONS
        else:
            options = SHARK_LOAN_OPTIONS

        option = options.get(option_key)
        if not option:
            return None

        principal = option["amount"]
        interest_rate = option["interest_rate"]
        weeks = option["weeks"]

        total_interest = int(principal * interest_rate)
        total_owed = principal + total_interest
        weekly_payment = max(1, total_owed // weeks)

        loan = Loan(
            id=f"loan_{self.next_id}",
            loan_type=loan_type,
            principal=principal,
            interest_rate=interest_rate,
            total_owed=total_owed,
            weekly_payment=weekly_payment,
            weeks_total=weeks,
            weeks_remaining=weeks,
            date_taken=date_str,
        )

        self.next_id += 1
        self.active_loans.append(loan)
        self.total_borrowed += principal

        return loan

    def process_weekly_payments(self, available_budget: int) -> Dict:
        """Process all weekly loan payments. Returns total deducted and messages."""
        total_deducted = 0
        messages = []
        payments_made = []

        for loan in self.active_loans:
            if loan.status != LoanStatus.ACTIVE:
                continue

            payment_due = loan.get_next_payment()

            if available_budget - total_deducted >= payment_due:
                # Can afford payment
                result = loan.make_payment(payment_due)
                total_deducted += payment_due
                self.total_interest_paid += max(0, payment_due - (loan.principal // loan.weeks_total))
                loan.penalty_active = False

                if result.get("paid_off"):
                    self.active_loans.remove(loan)
                    self.loan_history.append(loan)
                    self.credit_score = min(850, self.credit_score + 25)
                    messages.append(f"🎉 {loan.loan_type.value} paid off!")
                else:
                    messages.append(f"💰 {loan.loan_type.value}: ${payment_due:,} paid. ${loan.get_remaining_balance():,} remaining.")
                    self.credit_score = min(850, self.credit_score + 1)

                payments_made.append({"loan_id": loan.id, "amount": payment_due, "success": True})
            else:
                # Cannot afford payment
                result = loan.miss_payment()
                self.credit_score = max(300, self.credit_score - 15)
                messages.append(result["message"])
                payments_made.append({"loan_id": loan.id, "amount": 0, "success": False, "penalty": result.get("penalty", 0)})

                if result.get("defaulted"):
                    self.credit_score = max(300, self.credit_score - 50)
                    messages.append("🚨 LOAN DEFAULT! Your reputation has been seriously damaged!")

        return {
            "total_deducted": total_deducted,
            "messages": messages,
            "payments": payments_made,
        }

    def get_total_weekly_obligations(self) -> int:
        """Get total amount owed this week across all loans"""
        total = 0
        for loan in self.active_loans:
            if loan.status == LoanStatus.ACTIVE:
                total += loan.get_next_payment()
        return total

    def get_total_outstanding(self) -> int:
        """Get total remaining balance across all active loans"""
        return sum(l.get_remaining_balance() for l in self.active_loans if l.status == LoanStatus.ACTIVE)

    def get_active_bank_loans(self) -> List[Loan]:
        return [l for l in self.active_loans if l.loan_type == LoanType.BANK and l.status == LoanStatus.ACTIVE]

    def get_active_shark_loans(self) -> List[Loan]:
        return [l for l in self.active_loans if l.loan_type == LoanType.LOAN_SHARK and l.status == LoanStatus.ACTIVE]

    def get_credit_rating(self) -> str:
        if self.credit_score >= 750:
            return "Excellent"
        elif self.credit_score >= 650:
            return "Good"
        elif self.credit_score >= 550:
            return "Fair"
        elif self.credit_score >= 450:
            return "Poor"
        else:
            return "Very Poor"

    def get_credit_color(self) -> str:
        if self.credit_score >= 750:
            return "#10b981"
        elif self.credit_score >= 650:
            return "#3b82f6"
        elif self.credit_score >= 550:
            return "#f59e0b"
        elif self.credit_score >= 450:
            return "#ef4444"
        else:
            return "#7f1d1d"

    def to_dict(self) -> dict:
        return {
            "active_loans": [l.to_dict() for l in self.active_loans],
            "loan_history": [l.to_dict() for l in self.loan_history[-20:]],
            "next_id": self.next_id,
            "total_interest_paid": self.total_interest_paid,
            "total_borrowed": self.total_borrowed,
            "credit_score": self.credit_score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BankingManager":
        bm = cls()
        bm.next_id = data.get("next_id", 1)
        bm.total_interest_paid = data.get("total_interest_paid", 0)
        bm.total_borrowed = data.get("total_borrowed", 0)
        bm.credit_score = data.get("credit_score", 500)
        for ld in data.get("active_loans", []):
            bm.active_loans.append(Loan.from_dict(ld))
        for ld in data.get("loan_history", []):
            bm.loan_history.append(Loan.from_dict(ld))
        return bm
