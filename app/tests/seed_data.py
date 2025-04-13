from decimal import Decimal
import random
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.mlmodel_settings import MLModelSettingsDB
from db.models.request_history import RequestHistoryDB
from db.models.transaction import TransactionDB
from db.models.user_action_history import UserActionHistoryDB
from db.models.user_roles import UserRoleDB
from db.models.mlmodel import MLModelDB
from db.models.user import UserDB
from schemas.mlmodel import MLModelCreate
from schemas.user import UserCreate
from schemas.user_roles import UserRoleCreate
from schemas.mlmodel_settings import MLModelSettingCreate
from schemas.request_history import RequestHistoryCreate
from services.user_service import UserService
from services.transaction_service import TransactionService
from services.user_roles_service import UserRolesService
from services.user_action_history_service import UserActionHistoryService
from services.mlmodel_service import MLModelService
from services.mlmodel_settings_service import MLModelSettingsService
from services.request_history_service import RequestHistoryService


class AsyncTestDataSeeder:
    def __init__(self, async_session_factory):
        self.async_session_factory = async_session_factory

    async def _get_services(self, async_session_factory: AsyncSession):
        """Инициализация сервисов с текущей сессией"""
        return {
            "user": UserService(async_session_factory),
            "transaction": TransactionService(async_session_factory),
            "user_roles": UserRolesService(async_session_factory),
            "action_history": UserActionHistoryService(async_session_factory),
            "mlmodel": MLModelService(async_session_factory),
            "mlmodel_settings": MLModelSettingsService(async_session_factory),
            "request_history": RequestHistoryService(async_session_factory),
        }

    async def seed_all(self):
        """Заполнение всех тестовых данных"""
        services = await self._get_services(self.async_session_factory)
        await self.seed_users(services)
        await self.seed_ml_models(services)
        await self.seed_transactions(services)
        await self.seed_requests(services)

    async def seed_users(self, services, count=10):
        """Создание тестовых пользователей"""
        print("Seeding users...")
        roles = ["admin", "manager", "user", "analyst"]

        for i in range(1, count + 1):
            user_data = UserCreate(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password=f"password{i}",
                balance=Decimal(random.uniform(100, 1000)).quantize(Decimal("0.00")),
            )

            # Создаем пользователя
            user = await services["user"].register_user(user_data)

            # Назначаем роли
            if i == 1:  # Первый пользователь - админ
                await services["user_roles"].assign_role_to_user(
                    UserRoleCreate(user_id=user.id, role="admin")
                )
            elif i == 2:  # Второй - менеджер
                await services["user_roles"].assign_role_to_user(
                    UserRoleCreate(user_id=user.id, role="manager")
                )
            else:  # Остальные - обычные пользователи
                role = random.choice(roles[2:])
                await services["user_roles"].assign_role_to_user(
                    UserRoleCreate(user_id=user.id, role=role)
                )

            # Логируем несколько действий
            actions = ["login", "profile_update", "password_change"]
            for action in random.sample(actions, 2):
                await services["action_history"].log_action(
                    user_id=user.id, action_type=action, status="success"
                )

    async def seed_ml_models(self, services):
        """Создание тестовых ML-моделей"""
        print("Seeding ML models...")
        models = [
            MLModelCreate(
                name="Qwen/Qwen2-VL-2B-Instruct",
                input_type="text",
                output_type="generation",
                cost_per_request=Decimal("0.05"),
                description="Text generation model",
            ),
            MLModelCreate(
                name="Image Recognizer",
                input_type="image",
                output_type="detection",
                cost_per_request=Decimal("0.10"),
                description="Image recognition model",
            ),
            MLModelCreate(
                name="Sales Predictor",
                input_type="tabular",
                output_type="regression",
                cost_per_request=Decimal("0.20"),
                description="Sales prediction model",
            ),
        ]

        for model_data in models:
            model = await services["mlmodel"].create_model(model_data)

            # Добавляем настройки для модели
            settings = [
                MLModelSettingCreate(
                    model_id=model.id, parameter="temperature", parameter_value="0.7"
                ),
                MLModelSettingCreate(
                    model_id=model.id, parameter="max_tokens", parameter_value="1000"
                ),
                MLModelSettingCreate(
                    model_id=model.id, parameter="threshold", parameter_value="0.5"
                ),
            ]

            for setting in settings:
                await services["mlmodel_settings"].create_setting(setting)

    async def seed_transactions(self, services):
        """Создание тестовых транзакций"""
        print("Seeding transactions...")
        async with self.async_session_factory() as session:
            result = await session.execute(select(UserDB))
            users = result.scalars().all()

            for user in users:
                # Создаем несколько депозитов
                for _ in range(random.randint(1, 3)):
                    amount = Decimal(random.uniform(50, 500)).quantize(Decimal("0.00"))
                    await services["transaction"].process_deposit(
                        user_id=user.id, amount=amount, description=f"Deposit #{_ + 1}"
                    )

                # Создаем несколько списаний
                for _ in range(random.randint(1, 2)):
                    amount = Decimal(random.uniform(10, 100)).quantize(Decimal("0.00"))
                    user_db = await session.get(UserDB, user.id)
                    if user_db.balance >= amount:
                        await services["transaction"].process_withdrawal(
                            user_id=user.id,
                            amount=amount,
                            description=f"Withdrawal #{_ + 1}",
                        )

    async def seed_requests(self, services):
        """Создание тестовых запросов к моделям"""
        print("Seeding requests...")
        async with self.async_session_factory() as session:
            users_result = await session.execute(select(UserDB))
            users = users_result.scalars().all()

            models_result = await session.execute(select(MLModelDB))
            models = models_result.scalars().all()

            for user in users:
                for _ in range(random.randint(3, 7)):
                    model = random.choice(models)
                    request = await services["request_history"].create_request(
                        RequestHistoryCreate(
                            user_id=user.id,
                            model_id=model.id,
                            request_type=random.choice(["prediction", "custom"]),
                            input_data=f"{{'data': 'test_data_{_}'}}",
                        )
                    )

                    # Рандомно завершаем некоторые запросы
                    if random.random() > 0.3:  # 70% chance
                        status = random.choice(["completed", "failed"])
                        if status == "completed":
                            await services["request_history"].complete_request(
                                request_id=request.id,
                                output_data=f"{{'result': 'sample_output_{_}'}}",
                                metrics=f"{{'accuracy': {random.uniform(0.7, 0.99):.2f}}}",
                                execution_time_ms=random.randint(100, 1000),
                                cost=model.cost_per_request,
                            )
                        else:
                            await services["request_history"].fail_request(
                                request_id=request.id,
                                error_message="Processing error",
                                execution_time_ms=random.randint(50, 500),
                            )

    async def clear_database(self):
        """Очистка базы данных"""
        print("Clearing database...")
        async with self.async_session_factory() as session:
            await session.execute(delete(RequestHistoryDB))
            await session.execute(delete(MLModelSettingsDB))
            await session.execute(delete(MLModelDB))
            await session.execute(delete(UserActionHistoryDB))
            await session.execute(delete(UserRoleDB))
            await session.execute(delete(TransactionDB))
            await session.execute(delete(UserDB))
            await session.commit()

    async def test_services(self):
        """Тестирование работы сервисов"""
        print("\nTesting services...")
        services = await self._get_services(self.async_session_factory)
        async with self.async_session_factory() as session:

            # 1. Проверка пользователей
            users_result = await session.execute(select(UserDB))
            users = users_result.scalars().all()
            print(f"Created {len(users)} users")

            # 2. Проверка транзакций
            transactions_result = await session.execute(select(TransactionDB))
            transactions = transactions_result.scalars().all()
            print(f"Created {len(transactions)} transactions")

            # 3. Проверка баланса
            for user in users[:3]:  # Проверяем 3 первых пользователя
                user_read = await services["user"].get_user_by_id(user.id)
                transactions = await services["transaction"].get_user_transactions(
                    user.id
                )
                print(f"\nUser {user.username} (ID: {user.id})")
                print(f"Balance: {user_read.balance}")
                print(f"Transactions count: {len(transactions)}")

                # Проверяем депозит
                deposit_amount = Decimal("100.00")
                old_balance = user_read.balance
                await services["transaction"].process_deposit(user.id, deposit_amount)
                updated_user = await services["user"].get_user_by_id(user.id)
                print(
                    f"Deposit test: {old_balance} + {deposit_amount} = {updated_user.balance}"
                )

                # Проверяем вывод (если достаточно средств)
                if updated_user.balance >= Decimal("50.00"):
                    old_balance = updated_user.balance
                    await services["transaction"].process_withdrawal(
                        user.id, Decimal("50.00")
                    )
                    updated_user = await services["user"].get_user_by_id(user.id)
                    print(
                        f"Withdrawal test: {old_balance} - 50.00 = {updated_user.balance}"
                    )

            # 4. Проверка статистики
            for user in users[:1]:
                stats = await services["request_history"].get_user_stats(user.id)
                print(f"\nStats for user {user.username}:")
                print(f"Total requests: {stats['total_requests']}")
                print(f"Completed requests: {stats['completed_requests']}")
                print(f"Total cost: {stats['total_cost']}")


async def async_seed_and_test(async_session_factory):
    seeder = AsyncTestDataSeeder(async_session_factory)

    # Очистка базы данных (опционально)
    # await seeder.clear_database()

    # Заполнение данных
    await seeder.seed_all()

    # Тестирование сервисов
    await seeder.test_services()
