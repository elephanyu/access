# coding:utf-8
import time
import json
import ftplib
import urlparse
import logging
import traceback
import StringIO

import requests

from seemmo.common.coding import tran2UTF8
from conf.globals import HTTP_GET_TIMEOUT, HTTP_GET_RETRY_NUM, HTTP_POST_TIMEOUT, HTTP_POST_RETRY_NUM, HTTP_RETRY_SLEEP_TIME

def post(url, param=None, **kwargs):
    param_json = param and json.dumps(param)

    with requests.Session() as session:
        lasterr = ''
        for i in range(HTTP_POST_RETRY_NUM):
            try:
                resp = session.post(url, data=param_json, timeout=HTTP_POST_TIMEOUT, **kwargs)
                if resp.status_code == 200:
                    return resp
                else:
                    lasterr = 'status code %s' % resp.status_code
            except Exception as e:
                lasterr = e
                time.sleep(HTTP_RETRY_SLEEP_TIME)

        if param and param.has_key('imageData'):
            del param['imageData']
            logging.error('exception occurs when post url[%s], param[%s]. [%s]' % (url, json.dumps(param), lasterr))
        else:
            logging.error('exception occurs when post url[%s], param[%s]. [%s]' % (url, param_json, lasterr))
        return None


def get(url, param=None):
    param_json = param and json.dumps(param)

    with requests.Session() as session:
        lasterr = ''
        for i in range(HTTP_GET_RETRY_NUM):
            try:
                resp = session.get(url, data=param_json, timeout=HTTP_GET_TIMEOUT)
                if resp.status_code == 200:
                    return resp.content
                else:
                    lasterr = 'status code %s' % resp.status_code
            except Exception as e:
                lasterr = e
                time.sleep(HTTP_RETRY_SLEEP_TIME)

        if param:
            logging.error('exception occurs when get url[%s], param[%s]. [%s]' % (url, param_json, lasterr))
        else:
            logging.error('exception occurs when get url[%s]. [%s]' % (url, lasterr))
        return None

def ftpdown(url):
    for i in range(HTTP_POST_RETRY_NUM):
        urlps = urlparse.urlparse(url)
        if '@' not in urlps.netloc:
            user = ''
            passwd = ''
            host = urlps.netloc
            port = 21
        else:
            urlhead = urlps.netloc.split('@')
            if len(urlhead) != 2:
                logging.error('err ftpurl format: %s.' % (url))
                continue
            else:
                user, passwd = urlhead[0].split(':')
                if ':' not in urlhead[1]:
                    host = urlhead[1]
                    port = 21
                else:
                    host, port = urlhead[1].split(':')

        try:
            ftp = ftplib.FTP()
            ftp.connect(host=host, port=port, timeout=HTTP_GET_TIMEOUT)
            ftp.login(user=user, passwd=passwd)
        except Exception:
            logging.error(traceback.format_exc())
            continue
        try:
            buf = StringIO.StringIO()
            ftp.retrbinary('RETR ' + urlps.path, buf.write)
            ftp.close()
            return buf.getvalue()
        except Exception:
            logging.error(traceback.format_exc())
            continue
    logging.error('exception occurs when ftp get url[%s]' % (url))
    return None

def download(url):
    # request url must in utf-8 code, in unicode or str does not import
    start_url = url[:3]
    if start_url == 'htt':
        return get(tran2UTF8(url))
    elif start_url == 'ftp':
        return ftpdown(url)
    else:
        logging.error('unknown url format[%s].' % (url))
    return None