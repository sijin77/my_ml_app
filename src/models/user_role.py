class UserRole:
    def __init__(self, role_id: int, name: str, description: str):
        self.__role_id = role_id
        self.__name = name
        self.__description = description

    @property
    def role_id(self) -> int:
        return self.__role_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def description(self) -> str:
        return self.__description

    @name.setter
    def name(self, name: str):
        if name is None or name.strip() == "":
            raise ValueError("Не указано наименование роли")
        self.__name = name

    @description.setter
    def name(self, description: str):
        if description is None or description.strip() == "":
            raise ValueError("Не указано описание роли")
        self.__description = description
