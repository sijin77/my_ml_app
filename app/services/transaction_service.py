from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, select
from db.models.transaction import TransactionDB
from db.models.user import UserDB
from schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionDetailRead,
    TransactionUpdate,
)


class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    # --- Основные CRUD операции ---
    async def create_transaction(
        self, transaction_data: TransactionCreate
    ) -> TransactionRead:
        """Создание новой транзакции"""
        # Проверяем существование пользователя
        user = await self.db.get(UserDB, transaction_data.user_id)
        if not user:
            raise ValueError("User not found")

        db_transaction = TransactionDB(**transaction_data.model_dump())

        self.db.add(db_transaction)
        await self.db.commit()
        await self.db.refresh(db_transaction)

        return TransactionRead.model_validate(db_transaction)

    async def update_transaction(
        self, transaction_id: int, update_data: TransactionUpdate
    ) -> Optional[TransactionRead]:
        """Обновление данных транзакции"""
        transaction = await self.db.get(TransactionDB, transaction_id)
        if not transaction:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(transaction, field, value)

        # transaction.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(transaction)

        return TransactionRead.model_validate(transaction)

    async def complete_transaction(
        self, transaction_id: int
    ) -> Optional[TransactionRead]:
        """Завершение транзакции (установка статуса completed)"""
        result = await self.update_transaction(
            transaction_id, TransactionUpdate(status="completed")
        )
        return result

    # --- Методы получения данных ---
    async def get_transaction_by_id(
        self, transaction_id: int, include_details: bool = False
    ) -> Optional[TransactionRead | TransactionDetailRead]:
        """Получение транзакции по ID"""
        transaction = await self.db.get(TransactionDB, transaction_id)
        if not transaction:
            return None

        return self._map_to_read_model(transaction, include_details)

    async def get_user_transactions(
        self, user_id: int, limit: int = 100, include_details: bool = False
    ) -> List[TransactionRead | TransactionDetailRead]:
        """Получение транзакций пользователя"""
        stmt = (
            select(TransactionDB)
            .where(TransactionDB.user_id == user_id)
            .order_by(desc(TransactionDB.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        transactions = result.scalars().all()
        return [self._map_to_read_model(t, include_details) for t in transactions]

    async def get_pending_transactions(
        self, limit: int = 100, include_details: bool = False
    ) -> List[TransactionRead | TransactionDetailRead]:
        """Получение ожидающих транзакций"""
        stmt = (
            select(TransactionDB)
            .where(TransactionDB.status == "pending")
            .order_by(desc(TransactionDB.created_at))
            .limit(limit)
        )
        result = self.db.execute(stmt)
        transactions = result.scalars().all()

        return [self._map_to_read_model(t, include_details) for t in transactions]

    # --- Бизнес-логика ---
    async def process_deposit(
        self, user_id: int, amount: Decimal, description: Optional[str] = None
    ) -> TransactionDetailRead:
        """Обработка депозита средств"""
        # Создаем транзакцию
        transaction = await self.create_transaction(
            TransactionCreate(
                user_id=user_id,
                amount=amount,
                transaction_type="deposit",
                description=description or f"Deposit {amount}",
            )
        )
        # Обновляем баланс пользователя
        user = await self.db.get(UserDB, user_id)
        user.balance += amount
        await self.db.commit()
        # Завершаем транзакцию
        comlited_transaction = await self.complete_transaction(transaction.id)
        return TransactionDetailRead.model_validate(comlited_transaction)

    async def process_withdrawal(
        self, user_id: int, amount: Decimal, description: Optional[str] = None
    ) -> Optional[TransactionDetailRead]:
        """Обработка вывода средств"""
        user = await self.db.get(UserDB, user_id)

        # Проверяем достаточность средств
        if user.balance < amount:
            return None

        # Создаем транзакцию
        transaction = await self.create_transaction(
            TransactionCreate(
                user_id=user_id,
                amount=-amount,  # Отрицательная сумма для вывода
                transaction_type="withdrawal",
                description=description or f"Withdrawal {amount}",
            )
        )

        # Обновляем баланс пользователя
        user.balance -= amount
        await self.db.commit()

        # Завершаем транзакцию
        comleted_transaction = await self.complete_transaction(transaction.id)
        return TransactionDetailRead.model_validate(comleted_transaction)

    # --- Вспомогательные методы ---
    def _map_to_read_model(
        self, transaction: TransactionDB, include_details: bool = False
    ) -> TransactionRead | TransactionDetailRead:
        """Преобразование ORM модели в соответствующую DTO"""
        if include_details:
            return TransactionDetailRead.model_validate(transaction)
        return TransactionRead.model_validate(transaction)
