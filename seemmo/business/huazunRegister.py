# coding:utf-8
import re
import uuid
import json
import hashlib
import logging
import traceback

import requests

class Digester:
    def __init__(self, digestInfo=None, authConf=None):
        if isinstance(digestInfo, dict):
            self._realm = digestInfo['realm'] if digestInfo.has_key('realm') else ''
            self._nonce = digestInfo['nonce'] if digestInfo.has_key('nonce') else ''
            self._opaque = digestInfo['opaque'] if digestInfo.has_key('opaque') else ''
            self._qop = digestInfo['qop'] if digestInfo.has_key('qop') else ''
        else:
            self._realm = ''
            self._nonce = ''
            self._opaque = ''
            self._qop = ''
        if isinstance(authConf, dict):
            self._username = authConf['username'] if authConf.has_key('username') else ''
            self._password = authConf['password'] if authConf.has_key('password') else ''
            self._uri = authConf['uri'] if authConf.has_key('uri') else ''
            self._method = authConf['method'] if authConf.has_key('method') else ''
            self._cnonce = authConf['cnonce'] if authConf.has_key('cnonce') else ''
        else:
            self._username = ''
            self._password = ''
            self._uri = ''
            self._method = ''
            self._cnonce = ''
        self._nc = '00000001'

    def generateAuthString(self):
        ha1 = self._encryByMd5('%s:%s:%s' % (self._username,self._realm, self._password))
        ha2 = self._encryByMd5('%s:%s' % (self._method, self._uri))
        other = '%s:%s:%s:%s' % (self._nonce, self._nc, self._cnonce, self._qop)
        signature = '''Digest username="%s",realm="%s",qop="%s",nonce="%s",opaque="%s",uri="%s",response="%s",nc=%s,cnonce="%s"''' % (
            self._username,
            self._realm,
            self._qop,
            self._nonce,
            self._opaque,
            self._uri,
            self._encryByMd5('%s:%s:%s' % (ha1, other, ha2)),
            self._nc,
            self._cnonce
        )
        return signature

    def _encryByMd5(self,datastr):
        return hashlib.new("md5", datastr).hexdigest()

class Register:
    def __init__(self, resturl=None, username=None, passwd=None, identify=None):
        self._resturl = resturl
        self._username = username
        self._passwd = passwd
        self._identify = identify
        self._uri = '/VIID/System/Register'

    def _paseHeader(self, header):
        if header['WWW-Authenticate']:
            auth = header['WWW-Authenticate']
            result = re.findall('Digest realm="(?P<realm>.*?)", qop="(?P<qop>.*?)", nonce="(?P<nonce>.*?)"', auth, re.I|re.S)
            if result:
                # realm, qop, nonce = result[0]
                return result[0]
            else:
                logging.error('parse header WWW-Authenticate err: %s' % auth)
                return None
        else:
            logging.error('header has no WWW-Authenticate key: %s' % header)
            return None


    def _firstStep(self):
        with requests.Session() as session:
            header = {
                'Content-Type': 'application/json;charset=UTF-8'
            }
            response = session.post(self._resturl+self._uri, headers=header)
            if response.status_code == 401:
                #logging.debug(response.headers)
                headerparse = self._paseHeader(response.headers)
                if headerparse:
                    digestInfo = {
                        'realm': headerparse[0],
                        'qop': headerparse[1],
                        'nonce': headerparse[2]
                    }
                    logging.debug('register first step success: %s' % str(headerparse))
                    return digestInfo
                else:
                    logging.error('register first step err for header parse failed')
                    return None
            else:
                logging.error('register first step err for post failed status: %s' % response.status_code)
                return None

    def _secondStep(self, digestInfo):
        authConf = {
            'username': self._username,
            'password': self._passwd,
            'method': 'POST',
            'uri': self._uri,
            'cnonce': str(uuid.uuid1()).replace('-','')
        }
        #logging.debug(digestInfo)
        #logging.debug(authConf)
        digestObj = Digester(digestInfo=digestInfo, authConf=authConf)
        signature = digestObj.generateAuthString()
        #logging.debug(signature)
        header = {
            'Content-Type': 'application/viid+json',
            'Authorization': signature,
        }
        registerparam = {
            'RegisterObject': {
                "DeviceID": self._identify
            }
        }
        #logging.debug(str(header))
        #logging.debug(json.dumps(registerparam))
        with requests.Session() as session:
            response = session.post(self._resturl+self._uri, headers=header, data=json.dumps(registerparam))
            #logging.debug(response.content)
            if response.status_code == 200:
                logging.debug(response.content)
                res_data = json.loads(response.content)
                if res_data.has_key('ResponseStatusObject') and res_data['ResponseStatusObject']['StatusCode'] == 0:
                    logging.debug('register second step success')
                    return True
                else:
                    res_data = json.loads(response.content)
                    logging.error('register second step err for failed result: %s' % res_data['ResponseStatusObject']['StatusString'])
                    return False
            else:
                logging.error('register second step for post status: %s' % response.status_code)
                return False

    def register(self):
        digestInfo = self._firstStep()
        if digestInfo:
            return self._secondStep(digestInfo)
        else:
            return False
