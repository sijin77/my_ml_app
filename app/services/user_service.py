import bcrypt
from models.user import User
from models.transaction import Transaction
from models.request_history import RequestHistory


class UserService:
    @staticmethod
    def hash_password(password: str) -> str:
        if password is None or password.strip() == "":
            raise ValueError("Пароль не может быть пустым")
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed_password.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        if password is None or password.strip() == "":
            raise ValueError("Пароль не может быть пустым")
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    @staticmethod
    def create_user(
        user_id: int, username: str, email: str, password: str, balance: float = 0.0
    ) -> "User":
        if password is None or password.strip() == "":
            raise ValueError("Пароль не может быть пустым")
        hashed_password = UserService.hash_password(password)
        return User(user_id, username, email, hashed_password, balance)

    @staticmethod
    def update_balance(user: "User", amount: float):
        if amount is None:
            raise ValueError("Сумма не может быть None")
        user._User__balance += amount

    @staticmethod
    def add_transaction(user: "User", transaction: "Transaction"):
        if transaction is None:
            raise ValueError("Транзакция не может быть None")
        user._User__transactions.append(transaction)

    @staticmethod
    def add_request_history(user: "User", request: "RequestHistory"):
        if request is None:
            raise ValueError("Запрос не может быть None")
        user._User__request_history.append(request)
