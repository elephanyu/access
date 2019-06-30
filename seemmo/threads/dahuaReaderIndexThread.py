# coding=utf-8
import json
import logging
import traceback
from collections import deque
from Queue import Full as QueueFull

import requests

from seemmo.threads.baseThread import BaseThread
from conf.mapping import data_mapping
from conf.globals import *
from seemmo.common.time import *
from seemmo.common.utils import increase
from seemmo.common.config import Config

class DahuaReaderIndexThread(BaseThread):
    def __init__(self, output, proc_setting=None, stats=None):
        BaseThread.__init__(self, proc_setting=proc_setting, stats=stats)
        self.output = output
        self.preData = deque()
        self.config = Config('reader.cfg')
        self.current_index = int(self.config.get('current_index', 0))
        self.current_time = self.config.get('current_time', now())
        self.now = self.config.get('now')

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
        self.now = now()
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': self.proc_setting['setting']['authcode']
        }
        query_data = {
            'startId': self.current_index,
            'endId': (self.current_index + self.proc_setting['setting']['pagesize']),
            'page':{
                'pageNo': 1,
                'pageSize': self.proc_setting['setting']['pagesize']
            }
        }
        query_url = self.proc_setting['setting']['resturl'] + '?q=%s' % (json.dumps(query_data))
        session = requests.Session()
        try:
            response = session.get(url=query_url, headers=headers)
            if response and response.status_code == 200:
                res_data = json.loads(response.content)
                if res_data['code'] == 100:
                    rows = res_data['data']['rows']
                    logging.info('result.size: %s, startId: %s.' % (rows and len(rows), self.current_index))
                    if rows is not None and len(rows) > 1:
                        for row in rows[1:]:
                            data = data_mapping(row)
                            if data['id'] > self.current_index:
                                self.current_index = data['id']
                            if data['snapshotTime'] > to_mstimestamp(self.current_time):
                                self.current_time = to_string(data['snapshotTime'])
                            if data['ImageURL'] is None:
                                increase(self.stats, 'read_false_total', self.threadId)
                                # logging.error('Data image url error: %s' % str(row))
                                continue
                            if TOLL_FILTER_TYPE == 1:
                                if data['deviceId'] not in TOLLGATE_IDS:
                                    continue
                            elif TOLL_FILTER_TYPE == 2:
                                if data['deviceId'] in TOLLGATE_IDS:
                                    continue
                            self.preData.append(data)
                            # self.output.put(data, block=True)
                            # logging.info('enqueue new data: %s, %s' % (data['id'], data['ImageURL']))
                    else:
                        time.sleep(READ_EMPTY_SLEEP_TIME)
                        return
                else:
                    logging.error('exception occurs when access rest api, url: %s, response err: %s' % (query_url, res_data['msg']))
            else:
                logging.error('exception occurs when access rest api, url: %s, rest api may stopped!' % query_url)
        except Exception as e:
            logging.error('exception occurs when access rest api, url: %s, err: \n%s' % (query_url, traceback.format_exc()))
            return

        try:
            self.config.set('current_index', self.current_index)
            self.config.set('current_time', self.current_time)
            self.config.set('now', self.now)
            self.config.save()

        except Exception as e:
            logging.error("Failed to update config file %s: %s." % (self.config.filepath, e))
            self.current_index = int(self.config.get('current_index', 0))
            self.current_time = self.config.get('current_time', now())
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
                    # logging.debug('wait thread reader\'s predata to process, predata len : %s' % len(self.preData))
                    self.enqueueData()
                else:
                    break
        logging.debug('thread is stopped %s' % (self.name))

