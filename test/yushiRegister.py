# coding:utf-8
import os
import sys
import time
import json
import urllib
import traceback
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'packages'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'conf'))

import requests

from conf.settings import PROC_SETTING
from seemmo.business.yushiRegister import Register

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
    try:
        register = Register(
            resturl=PROC_SETTING['procs'][0]['proc']['setting']['resturl'],
            username=PROC_SETTING['procs'][0]['proc']['setting']['username'],
            passwd=PROC_SETTING['procs'][0]['proc']['setting']['passwd'],
        )
        token = register.getToken()
        logging.debug('the token: %s' % token)
    except Exception:
        print(traceback.format_exc())