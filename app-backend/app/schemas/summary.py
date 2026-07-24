from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    date_from: date
    date_to: date
    revenue: Decimal
    fuel_cost: Decimal
    other_expenses: Decimal
    profit: Decimal
