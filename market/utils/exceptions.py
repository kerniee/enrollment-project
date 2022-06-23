class HTTPException(Exception):
    def __init__(self, status_code: int, message):
        self.status_code = status_code
        self.message = message
