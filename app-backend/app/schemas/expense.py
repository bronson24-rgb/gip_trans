import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.expense import ExpenseCategory


class ExpenseCreate(BaseModel):
    expense_date: date
    category: ExpenseCategory
    amount: Decimal = Field(gt=0)
    comment: str | None = None


class ExpenseUpdate(BaseModel):
    expense_date: date | None = None
    category: ExpenseCategory | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    comment: str | None = None


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    expense_date: date
    category: ExpenseCategory
    amount: Decimal
    comment: str | None
    created_by: uuid.UUID
    created_at: datetime
