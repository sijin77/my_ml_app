import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Импортируем ваши модули (замените на актуальные пути)
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from services.user_service import UserService
from services.transaction_service import TransactionService
from db.base_model import Base

# Настройка тестовой базы данных (используем SQLite в памяти)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Фикстуры для работы с базой данных
@pytest_asyncio.fixture(scope="module")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    async_session = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )
    return async_session


@pytest_asyncio.fixture
async def user_service(session):
    return UserService(session)


@pytest_asyncio.fixture
async def transaction_service(session):
    return TransactionService(session)


@pytest.fixture
def valid_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword",
        "balance": "100.00",
    }
