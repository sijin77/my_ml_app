class MLModelSettings:
    def __init__(self, setting_id: int, model_id: int, parameter: str, value: str):
        self.__setting_id = setting_id
        self.__model_id = model_id
        self.__parameter = parameter
        self.__parameter_value = value

    @property
    def setting_id(self) -> int:
        return self.__setting_id

    @property
    def model_id(self) -> int:
        return self.__model_id

    @property
    def parameter(self) -> str:
        return self.__parameter

    @property
    def parameter_value(self) -> str:
        return self.__parameter_value

    @parameter_value.setter
    def value(self, value: str):
        if value is None or value.strip() == "":
            raise ValueError("пароль не может быть пустым")
        self.__parameter_value = value
