import os
from datetime import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGGING_DIR = os.path.join(BASE_DIR, "pcr_logs")
os.makedirs(LOGGING_DIR, exist_ok=True)
INTERVAL = 1
BACKUP_COUNT = 5
LOGGING_VERSION = 1

Filters = {
    "filter_info_level": {
        "()": "pcr.log_filters.FilterLevels",
        "filter_levels": ["INFO"],
    },
    "filter_error_level": {
        "()": "pcr.log_filters.FilterLevels",
        "filter_levels": ["ERROR"],
    },
    "filter_debug_level": {
        "()": "pcr.log_filters.FilterLevels",
        "filter_levels": ["DEBUG"],
    },
    "filter_warning_level": {
        "()": "pcr.log_filters.FilterLevels",
        "filter_levels": ["WARNING"],
    },
}

Formatter = {
    "verbose": {
        "format": "{levelname} {asctime} [{pathname}:{module}:{funcName}:{lineno}] {message}",
        "datefmt": "%Y-%m-%d %H:%M:%S",
        "style": "{",
    },
    "simple": {
        "format": "{levelname} {message}",
        "style": "{",
    },
}

log_types = [
    "pcr",
    "delivery",
]


def get_logger(filter_name, filename):
    """
    method to set the logger handler specification
    """

    return {
        "class": "concurrent_log_handler.ConcurrentTimedRotatingFileHandler",
        "formatter": "verbose",
        "filters": [filter_name],
        "filename": os.path.join(LOGGING_DIR, filename),
        "when": "midnight",
        "interval": INTERVAL,
        "backupCount": BACKUP_COUNT,  # number of backup files to keep
        "encoding": None,
        "delay": True,
        "utc": True,
        "errors": None,
        "atTime": time(0, 0),
    }


handlers = {}
for log_type in log_types:
    handlers[f"{log_type}_info_logger"] = get_logger(
        "filter_info_level", f"{log_type}_info.log"
    )

    handlers[f"{log_type}_error_logger"] = get_logger(
        "filter_error_level", f"{log_type}_error.log"
    )

    handlers[f"{log_type}_warning_logger"] = get_logger(
        "filter_warning_level", f"{log_type}_warning.log"
    )

    handlers[f"{log_type}_debug_logger"] = get_logger(
        "filter_debug_level", f"{log_type}_debug.log"
    )

handlers["console"] = {
    "class": "logging.StreamHandler",
    "level": "DEBUG",
    "formatter": "simple",
}

loggers = {}
for log_type in log_types:
    loggers[f"{log_type}_logger"] = {
        "handlers": [
            f"{log_type}_info_logger",
            f"{log_type}_error_logger",
            f"{log_type}_warning_logger",
            f"{log_type}_debug_logger",
            "console",
        ],
        "level": "DEBUG",
        "propagate": True,
    }
    # if log_type == "pcr":
    #     loggers[f"{log_type}_logger"]["handlers"].append("console")

LOGGING = {
    "version": LOGGING_VERSION,
    "disable_existing_loggers": False,
    "filters": Filters,
    "formatters": Formatter,
    "handlers": handlers,
    "loggers": loggers,
}
