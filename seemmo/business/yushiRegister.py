# coding:utf-8
import json
import base64
import hashlib
import logging
import traceback

import requests

class Register:
    def __init__(self, resturl=None, username=None, passwd=None):
        self._resturl = resturl
        self._username = username
        self._passwd = passwd

    def _encryByMd5(self, str):
        return hashlib.new("md5", str).hexdigest()

    def _get(self, url, headers=None):
        with requests.Session() as session:
            try:
                resp = session.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp
                else:
                    logging.error('exception occurs when query data, status_code: %s' % resp.status_code)
                    return None
            except Exception:
                logging.error('exception occurs when query data, err:\n%s' % traceback.format_exc())
                return None

    def _post(self, url, param=None, step=None):
        with requests.Session() as session:
            try:
                resp = session.post(url, json=param, timeout=10)
                if resp.status_code == 200:
                    return resp
                else:
                    logging.error('exception occurs when login %s step, status_code: %s' % (step, resp.status_code))
                    return None
            except Exception:
                logging.error('exception occurs when login %s step, err:\n%s' % (step, traceback.format_exc()))
                return None

    def getToken(self):
        ret1 = self._post(self._resturl + 'login', step=1)
        if ret1:
            accessCode = json.loads(ret1.content)['AccessCode']
            signature = self._encryByMd5(base64.b64encode(self._username + accessCode + self._encryByMd5(self._passwd)))
            data = {
                'UserName': self._username,
                'AccessCode': accessCode,
                'LoginSignature': signature
            }
            ret2 = self._post(self._resturl + 'login', param=data, step=2)
            if ret2:
                token = json.loads(ret2.content)['AccessToken']
                return token
            else:
                token = None
        else:
            token = None
        return token


