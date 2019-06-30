from __future__ import absolute_import
import os
from logging import Formatter, getLogger, DEBUG, INFO, WARNING, ERROR, CRITICAL

from ConcurrentLogHandler.cloghandler import ConcurrentRotatingFileHandler

from seemmo.common.paths import logging_path
from conf.globals import LOGGER_FILE_MAXBYTE, LOGGER_SET_LEVEL, DEBUG_BACK_COUNT, INFO_BACK_COUNT, WARNING_BACK_COUNT, ERROR_BACK_COUNT, CRITICAL_BACK_COUNT

def init(log_path=logging_path('server')):
    formatter = Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')

    debug = ConcurrentRotatingFileHandler(
        os.path.join(log_path, 'debug.log'),
        maxBytes=LOGGER_FILE_MAXBYTE,
        backupCount=DEBUG_BACK_COUNT)
    debug.setLevel(DEBUG)
    debug.setFormatter(formatter)

    info = ConcurrentRotatingFileHandler(
        os.path.join(log_path, 'info.log'),
        maxBytes=LOGGER_FILE_MAXBYTE,
        backupCount=INFO_BACK_COUNT)
    info.setLevel(INFO)
    info.setFormatter(formatter)

    # warning = ConcurrentRotatingFileHandler(
    #     os.path.join(log_path, 'warning.log'),
    #     maxBytes=LOGGER_FILE_MAXBYTE,
    #     backupCount=WARNING_BACK_COUNT)
    # warning.setLevel(WARNING)
    # warning.setFormatter(formatter)

    error = ConcurrentRotatingFileHandler(
        os.path.join(log_path, 'error.log'),
        maxBytes=LOGGER_FILE_MAXBYTE,
        backupCount=ERROR_BACK_COUNT)
    error.setLevel(ERROR)
    error.setFormatter(formatter)

    critical = ConcurrentRotatingFileHandler(
        os.path.join(log_path, 'critical.log'),
        maxBytes=LOGGER_FILE_MAXBYTE,
        backupCount=CRITICAL_BACK_COUNT)
    critical.setLevel(CRITICAL)
    crit_format = Formatter('%(asctime)s %(message)s')
    critical.setFormatter(crit_format)

    logger = getLogger('')
    logger.addHandler(debug)
    logger.addHandler(info)
    # logger.addHandler(warning)
    logger.addHandler(error)
    logger.addHandler(critical)
    if LOGGER_SET_LEVEL == 2:
        LEVEL = INFO
    elif LOGGER_SET_LEVEL == 3:
        LEVEL = WARNING
    elif LOGGER_SET_LEVEL == 4:
        LEVEL = ERROR
    elif LOGGER_SET_LEVEL == 5:
        LEVEL = CRITICAL
    else:
        LEVEL = DEBUG
    logger.setLevel(LEVEL)
