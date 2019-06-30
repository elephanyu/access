# coding:utf-8
import time
import json
import urllib2
import logging
import traceback

from seemmo.common.coding import tran2UTF8
from conf.globals import HTTP_GET_TIMEOUT, HTTP_GET_RETRY_NUM, HTTP_POST_TIMEOUT, HTTP_POST_RETRY_NUM, HTTP_RETRY_SLEEP_TIME

__author__ = 'fuxiangyu'

def post(url, param):
    param_json = param and json.dumps(param)
    headers = {'Content-Type': 'application/json'}
    req = urllib2.Request(url=url, headers=headers, data=param_json)
    lasterr = ''
    for i in range(HTTP_POST_RETRY_NUM):
        try:
            resp = urllib2.urlopen(req, timeout=HTTP_POST_TIMEOUT)
            if resp.getcode() == 200:
                ret = resp.read()
                resp.close()
                return ret
            else:
                lasterr = 'status code %s' % resp.status_code
        except Exception:
            lasterr = traceback.format_exc()
            time.sleep(HTTP_RETRY_SLEEP_TIME)

    if param and param.has_key('imageData'):
        del param['imageData']
        logging.error('exception occurs when post url[%s], param[%s]. [%s]' % (url, json.dumps(param), lasterr))
    else:
        logging.error('exception occurs when post url[%s], param[%s]. [%s]' % (url, param_json, lasterr))
    return None


def download(url):
    req = urllib2.Request(tran2UTF8(url))
    lasterr = ''
    for i in range(HTTP_GET_RETRY_NUM):
        try:
            resp = urllib2.urlopen(req, timeout=HTTP_GET_TIMEOUT)
            if resp.getcode() == 200:
                ret = resp.read()
                resp.close()
                return ret
            else:
                lasterr = 'status code %s' % resp.status_code
        except Exception:
            lasterr = traceback.format_exc()
            time.sleep(HTTP_RETRY_SLEEP_TIME)

    logging.error('exception occurs when get url[%s]. [%s]' % (url, lasterr))
    return None

if __name__ == '__main__':
    link = 'http://pic32.photophoto.cn/20140711/0011024086081224_b.jpg'
    result = download(link)
    if result:
        print result
