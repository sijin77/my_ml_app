class RequestHistory:
    def __init__(
        self,
        request_id: int,
        user_id: int,
        data: str,
        prediction: str,
        cost: float,
        timestamp: str,
    ):
        self.__request_id = request_id
        self.__user_id = user_id
        self.__data = data
        self.__prediction = prediction
        self.__cost = cost
        self.__timestamp = timestamp

    @property
    def request_id(self) -> int:
        return self.__request_id

    @property
    def user_id(self) -> int:
        return self.__user_id

    @property
    def data(self) -> str:
        return self.__data

    @property
    def prediction(self) -> str:
        return self.__prediction

    @property
    def cost(self) -> float:
        return self.__cost

    @property
    def timestamp(self) -> str:
        return self.__timestamp
