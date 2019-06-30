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

class DahuaReaderTimeTimeWalkhread(BaseThread):
    def __init__(self, output, proc_setting=None, stats=None):
        BaseThread.__init__(self, proc_setting=proc_setting, stats=stats)
        self.output = output
        self.preData = deque()
        self.repeatData = []
        self.config = Config('reader.cfg')
        self.current_time = self.config.get('current_time', now())
        self.current_index = int(self.config.get('current_index', 0))
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
        next_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.mktime(time.strptime(self.current_time, '%Y-%m-%d %H:%M:%S')) + READ_ONCE_WALK_TIME))
        if seconds_between(next_time, self.now) <= READ_RESERVE_TIME:
            time.sleep(READ_RESERVE_SLEEP_TIME)
            return
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': self.proc_setting['setting']['authcode']
        }
        query_data = {
            'startDate': self.current_time,
            'endDate': next_time,
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
                    logging.info('result.size: %s, startId: %s.' % (rows and len(rows), self.current_time))
                    if rows is not None and len(rows) > 0:
                        repeat_list = []
                        for row in rows:
                            data = data_mapping(row)
                            if data['snapshotTime'] == next_time:
                                repeat_list.append(data['id'])
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
                        self.repeatData = repeat_list
                        logging.debug('new repeat list: %s.' % str(self.repeatData))
                    self.current_time = next_time
                else:
                    logging.error('exception occurs when access rest api, url: %s, response err: %s' % (query_url, res_data['msg']))
            else:
                logging.error('exception occurs when access rest api, url: %s, rest api may stopped!' % query_url)
        except Exception:
            logging.error('exception occurs when access rest api, url: \n%s, err: %s' % (query_url, traceback.format_exc()))
            return

        try:
            self.config.set('current_time', self.current_time)
            self.config.set('now', self.now)
            self.config.save()

        except Exception as e:
            logging.error("Failed to update config file %s: %s." % (self.config.filepath, e))
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
                    logging.info('wait thread reader\'s predata to process, predata len : %s' % len(self.preData))
                    self.enqueueData()
                else:
                    break
        logging.debug('thread is stopped %s' % (self.name))

