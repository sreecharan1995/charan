"""
This is the logger used from everywhere. 

Logging is by default to console only, but in case an env var named LOG_FOLDER is set then, aditionally,
file logging will be enabled to that folder. The file holding logs will be named as the pod name (taken from HOSTNAME)
with .log sufixed.
"""

import os
import logging
from typing import List, Optional
from logging.config import dictConfig

_LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "DEBUG")
_LOG_HANDLERS: List[str] = ["console"] # only use console by default

_HOSTNAME: str = os.environ.get("HOSTNAME", "localhost") # hostname is taken from env, so pod name is used

_LOG_FOLDER: Optional[str] = os.environ.get("LOG_FOLDER", None) # if not set, file logging wont be enabled

log_file_path: str = "debug.log" # default name

if _LOG_FOLDER is not None: # use file logging only if LOG_FOLDER configured 
    log_file_path = os.path.join(_LOG_FOLDER, f"{_HOSTNAME}.log") # logging file name is autoconfigured based on hostname
    _LOG_HANDLERS.append("file") # include the file logging handler

_logger_config = {
    "version": 1,  # mandatory field
    # if you want to overwrite existing loggers' configs
    "disable_existing_loggers": False,
    "formatters": {
        "basic": {
            "format": "%(levelprefix)s %(asctime)s | %(message)s",
            "()": "uvicorn.logging.DefaultFormatter",
        }
    },
    "handlers": {
        "console": {
            "formatter": "basic",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "level": _LOG_LEVEL,
        },
        "file": {
            'formatter': 'basic',
            'class': 'logging.FileHandler',
            'filename': log_file_path or "debug.log",
            'mode': 'a',
            'level': _LOG_LEVEL,
        }
    },
    "loggers": {
        "custom": {
            "handlers": _LOG_HANDLERS,
            "level": _LOG_LEVEL,
            "propagate": False
        }
    },
}

dictConfig(_logger_config)
log: logging.Logger = logging.getLogger("custom")
"""The default logger used from everywhere
"""
