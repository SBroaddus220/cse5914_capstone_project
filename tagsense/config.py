# -*- coding: utf-8 -*-

"""
This module holds variables used by other modules.
The data here can be edited, just be careful.
"""

# **** IMPORTS ****
import logging
from pathlib import Path

# **** LOGGING ****
# Sets up logger
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------------------
# Should not be changed unless you know what you're doing
# ------------------------------------------------------------------------------------------

# **** PATHS ****
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "database.sqlite3"
CLIENT_FILES_DIR = DATA_DIR / "client_files"

# **** LOGGING CONFIGURATION ****
# Logging configurations
LOG_FILE_PATH = BASE_DIR / "program_log.txt"

LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # Doesn't disable other loggers that might be active
    "formatters": {
        "default": {
            "format": "[%(levelname)s][%(funcName)s] | %(asctime)s | %(message)s",
        },
        "simple": {  # Used for console logging
            "format": "[%(levelname)s][%(funcName)s] | %(message)s",
        },
    },
    "handlers": {
        "logfile": {
            "class": "logging.FileHandler",  # Basic file handler
            "formatter": "default",
            "level": "WARNING",
            "filename": LOG_FILE_PATH.as_posix(),
            "mode": "a",
            "encoding": "utf-8",
        },
        "console": {
            "class": "logging.StreamHandler",  # Basic stream handler
            "formatter": "simple",
            "level": "DEBUG",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {  # Simple program, so root logger uses all handlers
        "level": "DEBUG",
        "handlers": [
            "logfile",
            "console",
        ]
    }
}


# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
