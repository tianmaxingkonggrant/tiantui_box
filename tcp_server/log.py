__author__ = "wlj"
# create by wlj on 2021/2/25

import logging
import logging.handlers
import datetime

logger = logging.getLogger('mylogger')
logger.setLevel(logging.INFO)

f_handler = logging.FileHandler('gps.log')
f_handler.setLevel(logging.INFO)
f_handler.setFormatter(logging.Formatter("[%(asctime)s]-[%(levelname)s]-[%(filename)s - :%(lineno)d]: %(message)s"))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter("[%(asctime)s]-[%(levelname)s]-[%(filename)s - :%(lineno)d]: %(message)s"))

logger.addHandler(f_handler)
logger.addHandler(stream_handler)

