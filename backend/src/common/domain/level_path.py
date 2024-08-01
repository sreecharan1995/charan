 
from typing import Optional


class LevelPath:
    """Represents a canonized resource path.

    The path may not be correct or valid but its string representation is normalized.
    """

    _path: str

    def __init__(self, path: str):
        self._path = LevelPath.canonize(path)

    def get_path(self) -> str:
        return self._path

    @staticmethod
    def from_path(path: str) -> 'LevelPath':
        return LevelPath(path)

    @staticmethod
    def canonize(path: Optional[str] = "/") -> str:

        if path is None:
            return "/"

        path = path.strip()

        if path == "" or path == "/":
            return "/"

        while path.find("//") != -1:
            path = path.replace("//", "/")

        if path.endswith("/"):
            path = path[0:-1]

        if len(path) == 0:
            return "/"

        return path    