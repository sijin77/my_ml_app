from datetime import datetime


class Transaction:
    def __init__(
        self,
        transaction_id: int,
        user_id: int,
        amount: float,
        transaction_type: str,
        timestamp: datetime,
    ):
        self.__transaction_id = transaction_id
        self.__user_id = user_id
        self.__amount = amount
        self.__transaction_type = transaction_type
        self.__timestamp = timestamp

    @property
    def transaction_id(self) -> int:
        return self.__transaction_id

    @property
    def user_id(self) -> int:
        return self.__user_id

    @user_id.setter
    def user_id(self, value: int):
        if value is None:
            raise ValueError("Не указан пользователь")
        self.__user_id = value

    @property
    def amount(self) -> float:
        return self.__amount

    @amount.setter
    def amount(self, value: float):
        if value is None:
            raise ValueError("Не указана сумма операции")
        self.__amount = value

    @property
    def transaction_type(self) -> str:
        return self.__transaction_type

    @transaction_type.setter
    def transaction_type(self, value: str):
        if value is None or value.strip() == "":
            raise ValueError("Не указан тип операции")
        self.__transaction_type = value

    @property
    def timestamp(self) -> str:
        return self.__timestamp
