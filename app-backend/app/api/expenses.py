import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_driver
from app.database import get_db
from app.models.expense import Expense
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_driver),
) -> Expense:
    expense = Expense(**payload.model_dump(), created_by=user.id)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("", response_model=list[ExpenseRead])
def list_expenses(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_driver),
) -> list[Expense]:
    return db.query(Expense).order_by(Expense.expense_date.desc()).all()


@router.get("/{expense_id}", response_model=ExpenseRead)
def get_expense(
    expense_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_driver),
) -> Expense:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if expense is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Расход не найден")
    return expense


@router.patch("/{expense_id}", response_model=ExpenseRead)
def update_expense(
    expense_id: uuid.UUID,
    payload: ExpenseUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_driver),
) -> Expense:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if expense is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Расход не найден")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_driver),
) -> None:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if expense is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Расход не найден")

    db.delete(expense)
    db.commit()
