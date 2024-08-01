import datetime
import os
import random
import string
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from common.auth.auth_manager import APIKEY_PREFIX
from common.domain.level_path import LevelPath

from common.logger import log

import hashlib

class Utils:
    """This class contains miscelaneous static methods with utility to other shared and non-shared code
       of spinvfx microservice implementations.
    """

    @staticmethod
    def randomword(length: int):
        """Returns a random word of the specified length. Each word letter (a-z) will be in lowercase.
        """

        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for i in range(length))  # type: ignore

    @staticmethod
    def randomid(length: int):
        """Returns a random identifier of the specified length, formed by lowercase letters (a-z) or numbers (0-9).
        """

        letters = f"{string.ascii_lowercase}{string.digits}"
        return "".join(random.choice(letters) for i in range(length))  # type: ignore
    
    @staticmethod
    def derive_profile_id_from_path(path: str)-> str:
        
        encoded_path = LevelPath.canonize(path).encode()
        hash_obj = hashlib.sha1(encoded_path)
        
        return f"profile_{hash_obj.hexdigest()}"

    @staticmethod
    def get_current_date_time():
        """Returns the current system date formatted as YYYY-MM-DDTHH:MM:SS
        """

        return datetime.datetime.now().strftime("%Y-%b-%dT%H:%M:%S")

    @staticmethod
    def get_date_time(time_ns: int):
        """Returns the date represented by the nanosecods passed since the epoch, formatted as YYYY-MM-DDTHH:MM:SS
        """

        time_s = int(float(time_ns / (10 ** 9)))
        return datetime.datetime.fromtimestamp(time_s).strftime("%Y-%b-%dT%H:%M:%S")

    @staticmethod
    def file_age(filepath: str):
        """Returns the age of the specified file at path, in seconds
        """
        return time.time() - os.path.getmtime(filepath)

    @staticmethod
    def time_since(since: int, in_seconds: bool = False) -> float:
        """Returns the number of nanosecods or, optionally, seconds, that has passed since a timestamp expressed in seconds since the epoch
        """
        now: int = time.time_ns()
        ns: int = now - since
        if in_seconds:
            return ns / 10**9
        else:
            return ns

    @staticmethod
    def touch_file(filepath: str) -> bool:
        """Updates the date of the specified file 
        """
        try:
            Path(filepath).touch(mode=0o644, exist_ok=True)
        except BaseException:
            return False

        return True

    @staticmethod
    def simplify_token(token: Optional[str]) -> str:
        """Given a token or any other large enough string, it returns a simplified representation lacking most of its characters.

        Only the first 8 chars and the last 16 chars are shown.
        """
        if token is None:
            return ''

        if token.startswith(APIKEY_PREFIX):
            if len(token) > len(APIKEY_PREFIX) + 6:
                return f"{token[0:len(APIKEY_PREFIX) + 6]}..."
            else:
                return APIKEY_PREFIX
        
        if len(token) > 16:
            return f"{token[0:8]}...{token[-16:]}"
        else:
            return token
        
    @staticmethod    
    def check_max_file_age(tracking_file: str, max_allowed_file_age_in_seconds: int) -> int:

        try:
            file_age_in_seconds: float = Utils.file_age(f"{tracking_file}")
        except BaseException as e:
            log.error(f"UNHEALTY - Failed to find or read age of file {tracking_file}: {e}")
            return 2

        log.debug(f"Health check is verifying if file {tracking_file} is present and not older than {max_allowed_file_age_in_seconds} seconds")

        if file_age_in_seconds > max_allowed_file_age_in_seconds:
            log.warning(f"UNHEALTHY - File {tracking_file} age is {file_age_in_seconds} seconds")
            return 1

        log.info(f"HEALTHY - File {tracking_file} age is {file_age_in_seconds} seconds")

        return 0
    
    @staticmethod
    def read_from_env(var_name: str, def_value: Optional[str] = None) -> Optional[str]:

        return os.environ.get(var_name, default=def_value)

    @staticmethod
    def get_hostname() -> Optional[str]:

        return Utils.read_from_env(var_name="HOSTNAME")

    @staticmethod
    def register_docs(app: FastAPI):
        if os.path.isdir(".pdocs"):
            app.mount("/pdocs", StaticFiles(directory=".pdocs", html=True), name="pdocs")
