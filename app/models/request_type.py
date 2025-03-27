class RequestType:
    def __init__(self, type_id: int, name: str, description: str, cost: float):
        self.__type_id = type_id
        self.__name = name
        self.__description = description
        self.__cost = cost

    @property
    def type_id(self) -> int:
        return self.__type_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def description(self) -> str:
        return self.__description

    @property
    def cost(self) -> float:
        return self.__cost

    @name.setter
    def name(self, name: str):
        if name is None or name.strip() == "":
            raise ValueError("Не указано наименование категории запроса")
        self.__name = name

    @description.setter
    def name(self, description: str):
        if description is None or description.strip() == "":
            raise ValueError("Не указано описание категории")
        self.__description = description

    @cost.setter
    def cost(self, cost: float):
        if cost is None:
            cost = 0.0
        self.__cost = cost
