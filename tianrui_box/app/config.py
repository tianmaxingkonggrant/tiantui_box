import os, sys
from sanic.log import *

MAC_PRE = {"ec:2e:98": "Nvidia", "48:b0:2d": "Nvidia", "3a:81:f3": "FireFly"}
DB_CONFIG = {
    "tianrui_server_db": {
        "host": '192.168.240.227',
        "port": 3306,
        "user": 'root',
        "password": '123456',
        "db": "tianrui_server_db"
    },
    "vernemq_db": {
        "host": '192.168.240.227',
        "port": 3306,
        "user": 'root',
        "password": '123456',
        "db": "vernemq_db"
    }
}

# MQTT_CONFIG = {
#         "host": '192.168.240.228',
#         "port": 1883,
#         "user": 'admin',
#         "password": '123456'
# }

# DB_CONFIG = {
#     "tianrui_server_db": {
#         "host": '127.0.0.1',
#         "port": 3306,
#         "user": 'root',
#         "password": '123456',
#         "db": "tianrui_server_db"
#     },
#     "vernemq_db": {
#         "host": '127.0.0.1',
#         "port": 3306,
#         "user": 'root',
#         "password": '123456',
#         "db": "vernemq_db"
#     }
# }

MQTT_CONFIG = {
        "host": '127.0.0.1',
        "port": 1883,
        "user": 'admin',
        "password": '123456'
}



APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONFIG_DEFAULTS = dict(
    version=1,
    disable_existing_loggers=False,
    loggers={
        "sanic.root": {
            "level": "DEBUG",
            "handlers": []
        },
        "sanic.error": {
            "level": "INFO",
            "handlers": ["error_file", 'error_console'],
            "propagate": True,
            "qualname": "sanic.error",
        },
        "sanic.access": {
            "level": "INFO",
            "handlers": ["access_file", 'access_console'],
            "propagate": True,
            "qualname": "sanic.access",
        },
    },
    handlers={
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "access_formatter",
            "stream": sys.stdout,
        },
        "error_console": {
            "class": "logging.StreamHandler",
            "formatter": "error_formatter",
            "stream": sys.stderr,
        },
        "access_console": {
            "class": "logging.StreamHandler",
            "formatter": "access_formatter",
            "stream": sys.stdout,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": APP_DIR + "/logs/server_err.log",
            "formatter": "error_formatter",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 0,
            "encoding": "utf-8"
        },
        "access_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": APP_DIR + "/logs/server.log",
            "formatter": "access_formatter",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 0,
            "encoding": "utf-8"
        }
    },
    formatters={
        "error_formatter": {
            "format": "[%(asctime)s] %(message)s",
            "class": "logging.Formatter",
        },
        "access_formatter": {
            "format": "[%(asctime)s] %(message)s",
            "class": "logging.Formatter",
        },
    },
)
LOGGING_CONFIG_DEFAULTS_0 = dict(
    version=1,
    disable_existing_loggers=False,
    loggers={
        "sanic.root": {
            "level": "DEBUG",
            "handlers": []
        },
        "sanic.error": {
            "level": "INFO",
            "handlers": ['error_console'],
            "propagate": True,
            "qualname": "sanic.error",
        },
        "sanic.access": {
            "level": "INFO",
            "handlers": ['access_console'],
            "propagate": True,
            "qualname": "sanic.access",
        },
    },
    handlers={
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "access_formatter",
            "stream": sys.stdout,
        },
        "error_console": {
            "class": "logging.StreamHandler",
            "formatter": "error_formatter",
            "stream": sys.stderr,
        },
        "access_console": {
            "class": "logging.StreamHandler",
            "formatter": "access_formatter",
            "stream": sys.stdout,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": APP_DIR + "/logs/server_err.log",
            "formatter": "error_formatter",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 0,
            "encoding": "utf-8"
        },
        "access_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": APP_DIR + "/logs/server.log",
            "formatter": "access_formatter",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 0,
            "encoding": "utf-8"
        }
    },
    formatters={
        "error_formatter": {
            "format": "[%(asctime)s] %(message)s",
            "class": "logging.Formatter",
        },
        "access_formatter": {
            "format": "[%(asctime)s] %(message)s",
            "class": "logging.Formatter",
        },
    },
)