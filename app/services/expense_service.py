"""
Expense Ledger & Graph Debt Simplification Service (ARCH-7791, ARCH-7797).
Calculates exact splits, converts FX, and minimizes net transfer settlements across members.
"""

from typing import List, Dict, Any
from decimal import Decimal, ROUND_HALF_UP

# Active FX rates to base USD
EXCHANGE_RATES_TO_USD = {
    "USD": Decimal("1.0000"),
    "EUR": Decimal("1.0800"),
    "GBP": Decimal("1.2500"),
    "JPY": Decimal("0.006667"),  # ~150 JPY = 1 USD
    "CAD": Decimal("0.7300"),
    "AUD": Decimal("0.6500"),
    "CHF": Decimal("1.1200")
}

def convert_to_base_usd(amount: float, currency: str) -> Decimal:
    rate = EXCHANGE_RATES_TO_USD.get(currency.upper(), Decimal("1.0000"))
    return (Decimal(str(amount)) * rate).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

def simplify_debts(net_balances: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Minimizes total number of transactions between members using greedy debt reduction.
    net_balances: positive means member is owed money, negative means member owes money.
    """
    debtors = []   # (amount_owed_positive, member)
    creditors = [] # (amount_owed_to_member_positive, member)

    for member, bal in net_balances.items():
        val = round(bal, 2)
        if val < -0.01:
            debtors.append([-val, member])
        elif val > 0.01:
            creditors.append([val, member])

    debtors.sort(reverse=True, key=lambda x: x[0])
    creditors.sort(reverse=True, key=lambda x: x[0])

    settlements = []
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debt_amt, debtor = debtors[i]
        credit_amt, creditor = creditors[j]
        settle_amt = min(debt_amt, credit_amt)

        settlements.append({
            "from_user": debtor,
            "to_user": creditor,
            "amount": round(settle_amt, 2),
            "currency": "USD"
        })

        debtors[i][0] -= settle_amt
        creditors[j][0] -= settle_amt

        if debtors[i][0] < 0.01:
            i += 1
        if creditors[j][0] < 0.01:
            j += 1

    return settlements
