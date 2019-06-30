# coding=utf-8
import json
import logging
import traceback
from collections import deque
from Queue import Full as QueueFull

import pika

from seemmo.threads.baseThread import BaseThread
from conf.mapping import data_mapping
from conf.globals import *
from seemmo.common.time import *
from seemmo.common.utils import increase


class RabbitmqReaderThread(BaseThread):
    def __init__(self, output, proc_setting=None, stats=None):
        BaseThread.__init__(self, proc_setting=proc_setting, stats=stats)
        self.output = output
        self.preData = deque()

        logging.info("Reader[%s] init." % (self.name))

    def stop(self):
        self.exit.set()

    def new_connection(self):
        try:
            new_connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=self.proc_setting['setting']['ip'],
                port=self.proc_setting['setting']['port'],
                virtual_host=self.proc_setting['setting']['vhost'],
                credentials=pika.PlainCredentials(self.proc_setting['setting']['user'], self.proc_setting['setting']['password']),
                socket_timeout=READ_CONNECT_RETRY_TIME,
                frame_max=10000,
                channel_max=10,
            ))
            return new_connection
        except Exception:
            logging.error('database connect err:\n%s' % traceback.format_exc())
            return None

    def enqueueData(self):
        data = self.preData.popleft()
        try:
            self.output.put(data, block=False)
            logging.info('enqueue new data: %s, %s' % (data['id'], data['ImageURL']))
            increase(self.stats, 'read_success_total', self.threadId)
        except QueueFull:
            self.preData.appendleft(data)

    def fetchmany(self):
        fetch_start = time.time()
        connection = self.new_connection()
        if connection != None:
            try:
                channel = connection.channel(channel_number=int(self.name.split('-')[1]))
                channel.queue_declare(queue=self.proc_setting['setting']['que_name'], passive=True)
                while True:
                    if self.exit.is_set():
                        connection.close()
                        break
                    method, properties, body = channel.basic_get(self.proc_setting['setting']['que_name'])
                    if method is None:
                        connection.close()
                        if self.preData:
                            fetch_cost = round((time.time() - fetch_start) * 1000, 2)
                            logging.debug('fetch %s msg use %sms' % (len(self.preData), fetch_cost))
                        time.sleep(READ_EMPTY_SLEEP_TIME)
                        break
                    data = data_mapping(json.loads(body))
                    channel.basic_ack(method.delivery_tag)
                    if data['ImageURL'] is None:
                        increase(self.stats, 'read_false_total', self.threadId)
                    else:
                        if TOLL_FILTER_TYPE == 1:
                            if data['deviceId'] in TOLLGATE_IDS:
                                self.preData.append(data)
                        elif TOLL_FILTER_TYPE == 2:
                            if data['deviceId'] not in TOLLGATE_IDS:
                                self.preData.append(data)
                        else:
                            self.preData.append(data)
                    if method.delivery_tag == MQ_ONCE_COSUME_NUM:
                        connection.close()
                        fetch_cost = round((time.time() - fetch_start)*1000, 2)
                        logging.debug('fetch %s msg use %sms' % (len(self.preData), fetch_cost))
                        break
            except Exception:
                connection.close()
                logging.error(traceback.format_exc())

    def process(self):
        if self.preData:
            self.enqueueData()
            return
        self.fetchmany()

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
                    self.enqueueData()
                else:
                    break
        logging.debug('thread is stopped %s' % (self.name))
