# coding=utf-8
import json
import base64
import logging
import hashlib
import urllib
import traceback
from collections import deque
from Queue import Full as QueueFull

import requests

from conf.mapping import data_mapping
from conf.globals import *
from seemmo.common.time import *
from seemmo.common.config import Config
from seemmo.common.utils import increase
from seemmo.threads.baseThread import BaseThread
from seemmo.business.yushiRegister import Register


class YushiReaderTimeWalkThread(BaseThread):
    def __init__(self, output, proc_setting=None, stats=None):
        BaseThread.__init__(self, proc_setting=proc_setting, stats=stats)
        self.output = output
        self.preData = deque()
        self.repeatData = []
        self.config = Config('reader.cfg')
        self.current_startno = int(self.config.get('current_startno', 0))
        self.current_time = self.config.get('current_time', now())
        self.now = self.config.get('now')
        self.token = None

        logging.debug("Reader[%s] init." % (self.name))

    def enqueueData(self):
        one = self.preData.popleft()
        try:
            self.output.put(one, block=False)
            logging.info('enqueue new data: %s, %s' % (one['id'], one['ImageURL']))
            increase(self.stats, 'read_success_total', self.threadId)
        except QueueFull:
            self.preData.appendleft(one)
            return

    def process(self):
        if self.preData:
            self.enqueueData()
            return
        if self.token is None:
            register = Register(
                resturl=self.proc_setting['resturl'],
                username=self.proc_setting['username'],
                passwd=self.proc_setting['passwd'],
            )
            self.token = register.getToken()
            return
        self.now = now()
        next_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.mktime(time.strptime(self.current_time, '%Y-%m-%d %H:%M:%S')) + READ_ONCE_WALK_TIME))
        if seconds_between(next_time, self.now) <= READ_RESERVE_TIME:
            time.sleep(READ_RESERVE_SLEEP_TIME)
            return
        headers = {
            'Accept': '*/*',
            'authorization': self.token
        }
        condition = {
            "ItemNum": 2,
            "Condition": [{
                "QueryType": 356,
                "LogicFlag": 1,
                "QueryData": self.current_time
            }, {
                "QueryType": 356,
                "LogicFlag": 4,
                "QueryData": next_time
            }],
            "QueryCount": 0,
            "PageFirstRowNumber": self.current_startno,
            "PageRowNum": self.proc_setting['setting']['queryrow']
        }
        rescond = {
            "ResNum": 1,
            "ResList": [{
                "ResCode": "iccsid",
                "OrgCode": "",
                "ResIdCode": "",
                "ResName": "",
                "OrgName": "",
                "ResSubType": 10,
                "ResType": 1
            }]
        }
        queryUrl = self.proc_setting['setting']['resturl'] + 'query/vehicle?condition=' + urllib.quote(json.dumps(condition)) + '&rescond=' + urllib.quote(json.dumps(rescond))
        with requests.Session() as session:
            try:
                resp = session.get(queryUrl, headers=headers)
                if resp.status_code == 200:
                    result = json.loads(resp.content)
                    if result['ErrCode'] == 0:
                        logging.debug('current time: %s, start row: %s, result len: %s' % (self.current_time, self.current_startno, result['Result']['RspPageInfo']['RowNum']))
                        if result['Result']['RspPageInfo']['RowNum'] > 0:
                            for row in result['Result']['InfoList']:
                                data = data_mapping(row)
                                # if data['deviceId'] is None or data['deviceId'] not in TOLLGATE_IDS:
                                #     continue
                                if data['ImageURL'] is None:
                                    increase(self.stats, 'read_false_total', self.threadId)
                                    continue
                                if TOLL_FILTER_TYPE == 1:
                                    if data['deviceId'] not in TOLLGATE_IDS:
                                        continue
                                elif TOLL_FILTER_TYPE == 2:
                                    if data['deviceId'] in TOLLGATE_IDS:
                                        continue
                                self.preData.append(data)
                                self.current_startno = result['Result']['RspPageInfo']['TotalRowNum']
                        else:
                            self.current_time = next_time
                            self.current_startno = 0
                    else:
                        logging.error('exception occurs for get result err: %s' % resp.content)
                        self.token = None
                        return
                else:
                    logging.error('exception occurs for get status err: %s' % resp.status_code)
                    return
            except Exception:
                logging.error(traceback.format_exc())

        try:
            self.config.set('current_time', self.current_time)
            self.config.set('current_startno', self.current_startno)
            self.config.set('now', self.now)
            self.config.save()

        except Exception as e:
            logging.error("Failed to update config file %s: %s." % (self.config.filepath, e))
            self.current_time = self.config.get('current_time', now())
            self.current_startno = self.config.get('current_startno', 0)
            self.now = self.config.get('now')

    def run(self):
        logging.debug('thread is starting %s' % (self.name))
        while not self.exit.is_set():
            try:
                self.process()
            except Exception:
                logging.error('exception occurs when get data! %s' % (traceback.format_exc()))
                time.sleep(THREAD_PROCESS_RETRY_TIME)
        logging.debug('%s to stopping' % (self.name))
        if self.preData:
            while True:
                if self.preData:
                    logging.info('wait thread reader\'s predata to process, predata len : %s' % len(self.preData))
                    self.enqueueData()
                else:
                    break
        logging.debug('thread is stopped %s' % (self.name))

