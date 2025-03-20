from user import User
from datetime import datetime


class UserActionHistory:
    def __init__(self, action_id: int, user: User, action: str, timestamp: datetime):
        self.__action_id = action_id
        self.__user = user
        self.__action = action
        self.__timestamp = timestamp

    @property
    def action_id(self) -> int:
        return self.__action_id

    @property
    def user(self) -> User:
        return self.__user

    @property
    def action(self) -> str:
        return self.__action

    @property
    def timestamp(self) -> datetime:
        return self.__timestamp
