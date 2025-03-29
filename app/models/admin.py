from user import User
from transaction import Transaction


class Admin(User):
    def __init__(
        self,
        user_id: int,
        username: str,
        email: str,
        password_hash: str,
        balance: float = 0.0,
    ):
        super().__init__(user_id, username, email, password_hash, balance)
        self.__admin_transactions = []

    @property
    def admin_transactions(self) -> list:
        return self.__admin_transactions

    @admin_transactions.setter
    def admin_transaction(self, transaction: Transaction):
        self.__admin_transactions.append(transaction)
