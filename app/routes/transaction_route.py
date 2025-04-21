from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from services.transaction_service import TransactionService
from services.dependencies import get_transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/transactions/deposit")
async def deposit_funds(
    user_id: int,
    amount: Decimal,
    description: Optional[str] = None,
    service: TransactionService = Depends(get_transaction_service),
):
    try:
        return await service.process_deposit(user_id, amount, description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transactions/withdraw")
async def deposit_withdrawal(
    user_id: int,
    amount: Decimal,
    description: Optional[str] = None,
    service: TransactionService = Depends(get_transaction_service),
):
    try:
        return await service.process_withdrawal(user_id, amount, description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
