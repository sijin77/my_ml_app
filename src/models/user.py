from transaction import Transaction
from request_history import RequestHistory


class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        email: str,
        password_hash: str,
        balance: float = 0.0,
    ):
        self.__user_id = user_id
        self.__username = username
        self.__email = email
        self.__password_hash = password_hash
        self.__balance = balance
        self.__transactions = []
        self.__request_history = []

    @property
    def user_id(self) -> int:
        return self.__user_id

    @property
    def username(self) -> str:
        return self.__username

    @username.setter
    def username(self, value: str):
        if value is None or value.strip() == "":
            raise ValueError("Не указано имя пользователя")
        self.__username = value

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, value: str):
        if value is None or value.strip() == "":
            raise ValueError("Не указан mail пользователя")
        self.__email = value

    @property
    def password_hash(self) -> str:
        return self.__password_hash

    @password_hash.setter
    def password_hash(self, value: str):
        if value is None or value.strip() == "":
            raise ValueError("пароль не может быть пустым")
        self.__password_hash = value

    @property
    def balance(self) -> float:
        return self.__balance

    @property
    def transactions(self) -> list:
        return self.__transactions

    @property
    def request_history(self) -> list:
        return self.__request_history

    # Методы для добавления
    def add_transaction(self, transaction: Transaction):
        self.__transactions.append(transaction)

    def add_request_history(self, request: RequestHistory):
        self.__request_history.append(request)

    def update_balance(self, amount: float):
        self.__balance += amount
