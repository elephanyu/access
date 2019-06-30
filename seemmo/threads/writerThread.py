import json
import logging
import traceback
from random import randint
from Queue import Empty as QueueEmpty

from conf.globals import *
from seemmo.common.time import *
from seemmo.tools.requests_lib import post
# from seemmo.tools.pycurl_lib import post
from seemmo.common.utils import increase
from seemmo.threads.baseThread import BaseThread


class WriterThread(BaseThread):
    def __init__(self, input, proc_setting=None, stats=None):
        BaseThread.__init__(self, proc_setting=proc_setting, stats=stats)
        self.input = input
        self.service_url = self.proc_setting['setting']['service_url']
        logging.debug('writer[%s] init.' % (self.name))

    def process(self):
        try:
            input_data = self.input.get_nowait()
            input_data['imageUrl'] = input_data['IMageURL']
        except QueueEmpty:
            time.sleep(QUEUE_EMPTY_SLEEP_TIME)
            return
        if RUNNING_ENVIRON:
            write_start = time.time()
            post_result = post(self.service_url, param=input_data)
            write_cost = round((time.time() - write_start) * 1000, 2)
            if post_result is None:
                increase(self.stats, 'write_post_false_total', self.threadId)
                return
            result = json.loads(post_result.text)

            if not result['code'] == '0':
                if 'tollgate' in result['message']:
                    increase(self.stats, 'write_toll_false_total', self.threadId)
                else:
                    increase(self.stats, 'write_result_false_total', self.threadId)
                del input_data['imageData']
                logging.error('call vehicle service error. data[%s], result[%s], use time: %sms.'
                              % (json.dumps(input_data), result['message'], write_cost))
                return
            increase(self.stats, 'write_success_total', self.threadId)
            logging.info('new data send to vehicle service done! result: %s, id: %s, write time: %sms.' % ('True', input_data['id'], write_cost))
        else:
            seed = 1 if randint(1, 10) <= 9 else 0
            if seed:
                increase(self.stats, 'write_success_total', self.threadId)
                logging.info('new data send to vehicle service done! result: %s, id: %s.' % ('True', input_data['id']))
            else:
                increase(self.stats, 'write_post_false_total', self.threadId)
                logging.info('new data send to vehicle service done! result: %s, id: %s.' % ('False', input_data['id']))
