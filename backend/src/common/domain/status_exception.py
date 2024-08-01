
class StatusException(BaseException):
    """Extends exception to raise this type in certains cases where a code and message is required to be returned.
    """

    code: int
    message: str


    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message