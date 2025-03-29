from request_type import RequestType


class MLModel:
    def __init__(
        self, model_id: int, name: str, description: str, request_type: RequestType
    ):
        self.__model_id = model_id
        self.__name = name
        self.__description = description
        self.__request_type = request_type

    @property
    def model_id(self) -> int:
        return self.__model_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def description(self) -> str:
        return self.__description

    @property
    def request_type(self) -> RequestType:
        return self.__request_type

    @name.setter
    def name(self, name: str):
        if name is None or name.strip() == "":
            raise ValueError("Не указано наименование модели")
        self.__name = name

    @description.setter
    def name(self, description: str):
        if description is None or description.strip() == "":
            raise ValueError("Не указано описание модели")
        self.__description = description

    @request_type.setter
    def request_type(self, request_type: RequestType):
        self.__request_type = request_type
