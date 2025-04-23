from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import desc, select
from db.models.transaction import TransactionDB
from db.models.user import UserDB
from schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionDetailRead,
    TransactionUpdate,
)


from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import desc, select


class TransactionService:
    def __init__(self, async_session_factory: async_sessionmaker):
        self.async_session_factory = async_session_factory

    async def create_transaction(
        self, transaction_data: TransactionCreate
    ) -> TransactionRead:
        """Создание новой транзакции"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    # Проверка существования пользователя
                    user = await session.get(UserDB, transaction_data.user_id)
                    if not user:
                        raise ValueError("User not found")

                    # Создание транзакции
                    db_transaction = TransactionDB(**transaction_data.model_dump())
                    session.add(db_transaction)
                    await session.flush()
                    return TransactionRead.model_validate(db_transaction)
            except Exception:
                await session.rollback()
                raise

    async def update_transaction(
        self, transaction_id: int, update_data: TransactionUpdate
    ) -> Optional[TransactionRead]:
        """Обновление данных транзакции"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    transaction = await session.get(TransactionDB, transaction_id)
                    if not transaction:
                        return None

                    update_dict = update_data.model_dump(exclude_unset=True)
                    for field, value in update_dict.items():
                        setattr(transaction, field, value)

                    await session.flush()
                    return TransactionRead.model_validate(transaction)
            except Exception:
                await session.rollback()
                raise

    async def complete_transaction(
        self, transaction_id: int
    ) -> Optional[TransactionRead]:
        """Завершение транзакции"""
        return await self.update_transaction(
            transaction_id, TransactionUpdate(status="completed")
        )

    async def get_transaction_by_id(
        self, transaction_id: int, include_details: bool = False
    ) -> Optional[TransactionRead | TransactionDetailRead]:
        """Получение транзакции по ID"""
        async with self.async_session_factory() as session:
            transaction = await session.get(TransactionDB, transaction_id)
            if not transaction:
                return None

            if include_details:
                await session.refresh(transaction, ["user"])

            return self._map_to_read_model(transaction, include_details)

    async def get_user_transactions(
        self, user_id: int, limit: int = 100, include_details: bool = False
    ) -> List[TransactionRead | TransactionDetailRead]:
        """Получение транзакций пользователя"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(TransactionDB)
                .where(TransactionDB.user_id == user_id)
                .order_by(desc(TransactionDB.created_at))
                .limit(limit)
            )
            transactions = result.scalars().all()

            if include_details:
                for transaction in transactions:
                    await session.refresh(transaction, ["user"])

            return [self._map_to_read_model(t, include_details) for t in transactions]

    async def get_pending_transactions(
        self, limit: int = 100, include_details: bool = False
    ) -> List[TransactionRead | TransactionDetailRead]:
        """Получение ожидающих транзакций"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(TransactionDB)
                .where(TransactionDB.status == "pending")
                .order_by(desc(TransactionDB.created_at))
                .limit(limit)
            )
            transactions = result.scalars().all()

            if include_details:
                for transaction in transactions:
                    await session.refresh(transaction, ["user"])

            return [self._map_to_read_model(t, include_details) for t in transactions]

    async def process_deposit(
        self, user_id: int, amount: Decimal, description: Optional[str] = None
    ) -> TransactionDetailRead:
        """Обработка депозита средств"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    # Проверка существования пользователя
                    user = await session.get(UserDB, user_id)
                    if not user:
                        raise ValueError("User not found")

                    # Создаем транзакцию
                    transaction = await self._create_transaction_in_session(
                        session,
                        TransactionCreate(
                            user_id=user_id,
                            amount=amount,
                            transaction_type="deposit",
                            description=description or f"Deposit {amount}",
                        ),
                    )

                    # Обновляем баланс
                    user = await session.get(UserDB, user_id)
                    user.balance += amount

                    # Завершаем транзакцию
                    transaction.status = "completed"
                    await session.flush()
                    # await session.refresh(transaction, ["user"])

                    return TransactionRead.model_validate(transaction)
            except Exception as e:
                await session.rollback()
                raise

    async def process_withdrawal(
        self, user_id: int, amount: Decimal, description: Optional[str] = None
    ) -> Optional[TransactionDetailRead]:
        """Обработка вывода средств"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    user = await session.get(UserDB, user_id)

                    # Проверка баланса
                    if user.balance < amount:
                        raise ValueError("Insufficient balance")

                    # Создаем транзакцию
                    transaction = await self._create_transaction_in_session(
                        session,
                        TransactionCreate(
                            user_id=user_id,
                            amount=-amount,
                            transaction_type="withdrawal",
                            description=description or f"Withdrawal {amount}",
                        ),
                    )

                    # Обновляем баланс
                    user.balance = user.balance - amount

                    # Завершаем транзакцию
                    transaction.status = "completed"
                    await session.flush()
                    await session.refresh(transaction, ["user"])
                    await session.refresh(user)
                    return TransactionRead.model_validate(transaction)
            except Exception:
                await session.rollback()
                raise

    async def _create_transaction_in_session(
        self, session: AsyncSession, transaction_data: TransactionCreate
    ) -> TransactionDB:
        """Вспомогательный метод для создания транзакции в существующей сессии"""
        db_transaction = TransactionDB(**transaction_data.model_dump())
        session.add(db_transaction)
        await session.flush()
        await session.refresh(db_transaction)
        return db_transaction

    def _map_to_read_model(
        self, transaction: TransactionDB, include_details: bool = False
    ) -> TransactionRead | TransactionDetailRead:
        """Преобразование ORM модели в DTO"""
        if include_details:
            return TransactionDetailRead.model_validate(transaction)
        return TransactionRead.model_validate(transaction)
