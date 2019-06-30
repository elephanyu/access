import json
import logging
import traceback
from Queue import Full as QueueFull

import stompy
from stompy.frame import NOResponseError

from conf.globals import *
from conf.mapping import data_mapping
from seemmo.common.time import *
from seemmo.common.utils import increase
from seemmo.threads.baseThread import BaseThread

class ActivemqReaderThread(BaseThread):
    def __init__(self, output, stats, proc_setting):
        BaseThread.__init__(self)
        self.output = output
        self.proc_setting = proc_setting
        self.stats = stats
        self.preData = None
        logging.info('Reader[%s] init.' % (self.name))

    def new_connection(self):
        stompClient = stompy.Stomp(hostname=self.proc_setting['setting']['ip'],
                                   port=self.proc_setting['setting']['port'])
        stompClient.connect(username=self.proc_setting['setting']['user'],
                            password=self.proc_setting['setting']['password'])
        return stompClient

    def enqueueData(self):
        try:
            self.output.put(self.preData, block=False)
            logging.info('enqueue new data: %s, %s' % (self.preData['id'], self.preData['ImageURL']))
            increase(self.stats, 'read_success_total', self.threadId)
            self.preData = None
        except QueueFull:
            self.preData.appendleft(self.preData)

    def fetchone(self):
        connection = None
        try:
            connect_time_start = time.time()
            connection = self.new_connection()
            connect_time_cost = (time.time() - connect_time_start) * 1000
            connection.subscribe({
                    'destination': self.proc_setting['setting']['que_name'],
                    'ack': 'client'
                })
            time_start = time.time()
            frame = connection.receive_frame()
            receive_time_cost = (time.time() - time_start) * 1000
            connection.ack(frame)
            logging.debug('get one data from queue:%s,connect:%dms,receive:%dms' % (self.proc_setting['setting']['que_name'],connect_time_cost, receive_time_cost))
            if frame.body:
                data = data_mapping(json.loads(frame.body))
                if data['ImageURL'] is None:
                    increase(self.stats, 'read_false_total', self.threadId)
                elif TOLL_FILTER_TYPE == 1:
                    if data['deviceId'] in TOLLGATE_IDS:
                        self.preData = data
                elif TOLL_FILTER_TYPE == 2:
                    if data['deviceId'] not in TOLLGATE_IDS:
                        self.preData = data
                else:
                    self.preData = data
        except NOResponseError:
            logging.debug("get no data in 5s")
        except Exception:
            logging.error("exception happend when process %s" % (traceback.format_exc()))
        finally:
            if connection:
                connection.disconnect()

    def process(self):
        if self.preData:
            self.enqueueData()
            return
        self.fetchone()
