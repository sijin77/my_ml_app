# tests/seed_data.py
from decimal import Decimal
import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.mlmodel import MLModelCreate
from schemas.user import UserCreate
from schemas.user_roles import UserRoleCreate
from schemas.mlmodel_settings import MLModelSettingCreate
from schemas.request_history import RequestHistoryCreate
from db.models.user import UserDB
from db.models.transaction import TransactionDB
from db.models.user_roles import UserRoleDB
from db.models.user_action_history import UserActionHistoryDB
from db.models.mlmodel import MLModelDB, ModelInputTypeDB, ModelOutputTypeDB
from db.models.mlmodel_settings import MLModelSettingsDB
from db.models.request_history import RequestHistoryDB, RequestStatusDB, RequestTypeDB
from services.user_service import UserService
from services.transaction_service import TransactionService
from services.user_roles_service import UserRolesService
from services.user_action_history_service import UserActionHistoryService
from services.mlmodel_service import MLModelService
from services.mlmodel_settings_service import MLModelSettingsService
from services.request_history_service import RequestHistoryService
from fastapi import Depends


class AsyncTestDataSeeder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
        self.transaction_service = TransactionService(db)
        self.user_roles_service = UserRolesService(db)
        self.action_service = UserActionHistoryService(db)
        self.model_service = MLModelService(db)
        self.settings_service = MLModelSettingsService(db)
        self.request_service = RequestHistoryService(db)

    async def seed_all(self):
        """Заполнение всех тестовых данных"""
        await self.seed_users()
        await self.seed_ml_models()
        await self.seed_transactions()
        await self.seed_requests()

    async def seed_users(self, count=10):
        """Создание тестовых пользователей"""
        print("Seeding users...")
        roles = ["admin", "manager", "user", "analyst"]

        for i in range(1, count + 1):
            user_data = {
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "password": f"password{i}",
                "balance": Decimal(random.uniform(100, 1000)).quantize(Decimal("0.00")),
            }

            # Создаем пользователя
            user = await self.user_service.register_user(UserCreate(**user_data))

            # Назначаем роли
            if i == 1:  # Первый пользователь - админ
                await self.user_roles_service.assign_role_to_user(
                    UserRoleCreate(user_id=user.id, role="admin")
                )
            elif i == 2:  # Второй - менеджер
                await self.user_roles_service.assign_role_to_user(
                    UserRoleCreate(user_id=user.id, role="manager")
                )
            else:  # Остальные - обычные пользователи
                role = random.choice(roles[2:])
                await self.user_roles_service.assign_role_to_user(
                    UserRoleCreate(user_id=user.id, role=role)
                )

            # Логируем несколько действий
            actions = ["login", "profile_update", "password_change"]
            for action in random.sample(actions, 2):
                await self.action_service.log_action(
                    user_id=user.id, action_type=action, status="success"
                )

    async def seed_ml_models(self):
        """Создание тестовых ML-моделей"""
        print("Seeding ML models...")
        models = [
            {
                "name": "Text Classifier",
                "input_type": "text",
                "output_type": "classification",
                "cost_per_request": Decimal("0.05"),
                "description": "Text classification model",
            },
            {
                "name": "Image Recognizer",
                "input_type": "image",
                "output_type": "detection",
                "cost_per_request": Decimal("0.10"),
                "description": "Image recognition model",
            },
            {
                "name": "Sales Predictor",
                "input_type": "tabular",
                "output_type": "regression",
                "cost_per_request": Decimal("0.20"),
                "description": "Sales prediction model",
            },
        ]

        for model_data in models:
            model = await self.model_service.create_model(MLModelCreate(**model_data))

            # Добавляем настройки для модели
            settings = [
                {"parameter": "temperature", "parameter_value": "0.7"},
                {"parameter": "max_tokens", "parameter_value": "1000"},
                {"parameter": "threshold", "parameter_value": "0.5"},
            ]

            for setting in settings:
                await self.settings_service.create_setting(
                    MLModelSettingCreate(model_id=model.id, **setting)
                )

    async def seed_transactions(self):
        """Создание тестовых транзакций"""
        print("Seeding transactions...")
        result = await self.db.execute(select(UserDB))
        users = result.scalars().all()
        users_tupled = [(user.id) for user in users]
        for user_tupled in users_tupled:
            # Создаем несколько депозитов
            for _ in range(random.randint(1, 3)):
                amount = Decimal(random.uniform(50, 500)).quantize(Decimal("0.00"))
                await self.transaction_service.process_deposit(
                    user_id=user_tupled, amount=amount, description=f"Deposit #{_ + 1}"
                )

            # Создаем несколько списаний
            for _ in range(random.randint(1, 2)):
                amount = Decimal(random.uniform(10, 100)).quantize(Decimal("0.00"))
                user = await self.db.get(UserDB, user_tupled)
                if user.balance >= amount:
                    await self.transaction_service.process_withdrawal(
                        user_id=user_tupled,
                        amount=amount,
                        description=f"Withdrawal #{_ + 1}",
                    )

    async def seed_requests(self):
        """Создание тестовых запросов к моделям"""
        print("Seeding requests...")
        users_result = await self.db.execute(select(UserDB))
        users = users_result.scalars().all()

        users_tupled = [(user.id) for user in users]

        models_result = await self.db.execute(select(MLModelDB))
        models = models_result.scalars().all()
        models_tupled = [(model.id, model.cost_per_request) for model in models]
        for user_tupled in users_tupled:
            for _ in range(random.randint(3, 7)):
                model_rnd = random.choice(models_tupled)
                request = await self.request_service.create_request(
                    RequestHistoryCreate(
                        user_id=user_tupled,
                        model_id=model_rnd[0],
                        request_type=random.choice(["prediction", "custom"]),
                        input_data=f"{{'data': 'test_data_{_}'}}",
                    )
                )

                # Рандомно завершаем некоторые запросы
                if random.random() > 0.3:  # 70% chance
                    status = random.choice(["completed", "failed"])
                    if status == "completed":
                        await self.request_service.complete_request(
                            request_id=request.id,
                            output_data=f"{{'result': 'sample_output_{_}'}}",
                            metrics=f"{{'accuracy': {random.uniform(0.7, 0.99):.2f}}}",
                            execution_time_ms=random.randint(100, 1000),
                            cost=model_rnd[1],
                        )
                    else:
                        await self.request_service.fail_request(
                            request_id=request.id,
                            error_message="Processing error",
                            execution_time_ms=random.randint(50, 500),
                        )

    async def test_services(self):
        """Тестирование работы сервисов"""
        print("\nTesting services...")

        # 1. Проверка пользователей
        users_result = await self.db.execute(select(UserDB))
        users = users_result.scalars().all()
        print(f"Created {len(users)} users")

        # 2. Проверка транзакций
        transactions_result = await self.db.execute(select(TransactionDB))
        transactions = transactions_result.scalars().all()
        print(f"Created {len(transactions)} transactions")

        # 3. Проверка баланса
        for user in users[:1]:  # Проверяем первого пользователя
            user_read = await self.user_service.get_user_by_id(user.id)
            transactions = await self.transaction_service.get_user_transactions(user.id)
            print(f"\nUser {user.username} (ID: {user.id})")
            print(f"Balance: {user_read.balance}")
            print(f"Transactions count: {len(transactions)}")

            # Проверяем депозит
            deposit_amount = Decimal("100.00")
            old_balance = user_read.balance
            await self.transaction_service.process_deposit(user.id, deposit_amount)
            updated_user = await self.user_service.get_user_by_id(user.id)
            print(
                f"Deposit test: {old_balance} + {deposit_amount} = {updated_user.balance}"
            )

            # Проверяем вывод (если достаточно средств)
            if updated_user.balance >= Decimal("50.00"):
                old_balance = updated_user.balance
                await self.transaction_service.process_withdrawal(
                    user.id, Decimal("50.00")
                )
                updated_user = await self.user_service.get_user_by_id(user.id)
                print(
                    f"Withdrawal test: {old_balance} - 50.00 = {updated_user.balance}"
                )

        # 4. Проверка статистики
        for user in users[:1]:
            stats = await self.request_service.get_user_stats(user.id)
            print(f"\nStats for user {user.username}:")
            print(f"Total requests: {stats['total_requests']}")
            print(f"Completed requests: {stats['completed_requests']}")
            print(f"Total cost: {stats['total_cost']}")


async def async_seed_and_test(db: AsyncSession):
    seeder = AsyncTestDataSeeder(db)
    # Очистка базы данных (осторожно!)
    # await db.execute(delete(RequestHistoryDB))
    # await db.execute(delete(MLModelSettingsDB))
    # await db.execute(delete(MLModelDB))
    # await db.execute(delete(UserActionHistoryDB))
    # await db.execute(delete(UserRoleDB))
    # await db.execute(delete(TransactionDB))
    # await db.execute(delete(UserDB))
    # await db.commit()

    # Заполнение данных
    await seeder.seed_all()

    # Тестирование сервисов
    await seeder.test_services()
