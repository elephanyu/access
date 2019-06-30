# coding=utf-8
import logging
import traceback
from collections import deque
from Queue import Full as QueueFull

import psycopg2

from seemmo.threads.baseThread import BaseThread
from conf.mapping import data_mapping
from conf.globals import *
from seemmo.common.time import *
from seemmo.common.utils import increase
from seemmo.common.config import Config

class PostgresqlReaderIndexThread(BaseThread):
    def __init__(self, output, proc_setting=None, stats=None):
        BaseThread.__init__(self, proc_setting=proc_setting, stats=stats)
        self.output = output
        self.preData = deque()
        self.config = Config('reader.cfg')
        self.current_time = self.config.get('current_time', now())
        self.current_index = int(self.config.get('current_index', 0))
        self.now = self.config.get('now')

        logging.debug("Reader[%s] init." % (self.name))

    def new_connection(self):
        try:
            new_connection = psycopg2.connect(
                host=self.proc_setting['setting']['ip'],
                port=self.proc_setting['setting']['port'],
                user=self.proc_setting['setting']['user'],
                password=self.proc_setting['setting']['password'],
                dbname=self.proc_setting['setting']['dbname'],
                connect_timeout=READ_CONNECT_RETRY_TIME,
                # client_encoding='utf-8',
            )
            return new_connection
        except Exception:
            logging.error('database connect err:\n%s' % traceback.format_exc())
            return None

    def enqueueData(self):
        one = self.preData.popleft()
        try:
            self.output.put(one, block=False)
            logging.info('enqueue new data: %s, %s' % (one['deviceId'], one['ImageURL']))
            increase(self.stats, 'read_success_total', self.threadId)
        except QueueFull:
            self.preData.appendleft(one)
            return

    def process(self):
        if self.preData:
            self.enqueueData()
            return
        self.now = now()
        exec_sql = self.proc_setting['setting']['query_temp'] % self.current_index
        query_start = time.time()
        try:
            connection = self.new_connection()
            if connection == None:
                # time.sleep(READ_CONNECT_RETRY_TIME)
                return
            cursor = connection.cursor()
            cursor.execute(exec_sql)
            rows = cursor.fetchall()
            connection.close()
        except Exception as e:
            query_cost = round((time.time() - query_start) * 1000, 2)
            logging.error('err occurs when exec sql: %s, use time: %sms, sql: %s' % (e, query_cost, exec_sql))
            return
        query_cost = round((time.time() - query_start) * 1000, 2)
        logging.info('read time: %sms, result.size: %s <== sql: %s' % (query_cost, rows and len(rows), exec_sql))

        if rows is not None and len(rows) != 0:
            for row in rows:
                data = data_mapping(row)
                if data['id'] > self.current_index:
                    self.current_index = data['id']
                if data['ImageURL'] is None:
                    increase(self.stats, 'read_false_total', self.threadId)
                    continue
                if data['snapshotTime'] > to_mstimestamp(self.current_time):
                    self.current_time = to_string(data['snapshotTime'])
                if TOLL_FILTER_TYPE == 1:
                    if data['deviceId'] not in TOLLGATE_IDS:
                        continue
                elif TOLL_FILTER_TYPE == 2:
                    if data['deviceId'] in TOLLGATE_IDS:
                        continue
                self.preData.append(data)
        else:
            time.sleep(READ_EMPTY_SLEEP_TIME)
            return
        try:
            self.config.set('current_index', self.current_index)
            self.config.set('current_time', self.current_time)
            self.config.set('now', self.now)
            self.config.save()

        except Exception as e:
            self.current_index = self.config.get('current_id')
            self.current_time = self.config.get('current_time', now())
            logging.error("Failed to update config file %s: %s." % (self.config.filepath, e))
            return

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
                    logging.debug('wait thread reader\'s predata to process, predata len : %s' % len(self.preData))
                    self.enqueueData()
                else:
                    break
        logging.debug('thread is stopped %s' % (self.name))