# coding:utf-8
from __future__ import absolute_import
import os
import json
import time
import logging
import traceback
import threading

from seemmo.common.time import *

# err record in file to recycle
def fileRecord(srcdata, errType):
    try:
        dir_path = os.path.join(os.getcwd(), 'record')
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        filename = 'record_' + time.strftime('%Y%m%d', time.localtime(time.time())) + '.csv'
        file_path = os.path.join(dir_path, filename)
        lock = threading.Lock()
        lock.acquire()
        with open(file_path, 'a') as fp:
            if isinstance(srcdata, dict):
                rec_data = ''
                rec_data += 'id,' + srcdata['id']
                rec_data += ',time,' + time.strftime(default_format, time.localtime(srcdata['snapshotTime'] / 1000))
                rec_data += ',type,' + errType
                fp.write(rec_data + '\n')
            elif isinstance(srcdata, basestring):
                fp.write(srcdata + ',type,' + errType + '\n')
            else:
                fp.write(str(srcdata) + ',type,' + errType + '\n')
        lock.release()
    except Exception:
        logging.error(traceback.format_exc())

# err reput to queue
def reputRecord(srcdata, quename):
    try:
        if isinstance(srcdata, dict):
            quename.put(srcdata, block=True)
        else:
            pass
    except Exception:
        logging.error(traceback.format_exc())