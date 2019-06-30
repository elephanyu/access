import sys
import base64
import logging
from Queue import Empty as QueueEmpty, Full as QueueFull

from seemmo.tools.requests_lib import download
# from seemmo.tools.pycurl_lib import download
from seemmo.threads.baseThread import BaseThread
from seemmo.common.time import *
from seemmo.common.utils import increase
from conf.globals import QUEUE_EMPTY_SLEEP_TIME

class DownloaderThread(BaseThread):
    def __init__(self, input, output, proc_setting=None, stats=None):
        BaseThread.__init__(self, proc_setting=proc_setting, stats=stats)
        self.input = input
        self.output = output
        self.preData = None
        logging.debug('Downloader[%s] init' % (self.name))

    def enqueueData(self):
        try:
            self.output.put(self.preData, block=False)
            increase(self.stats, 'down_success_total', self.threadId)
            logging.info('enqueue new data: %s, %s.' % (self.preData['id'], self.preData['ImageURL']))
            self.preData = None
        except QueueFull:
            pass

    def process(self):
        try:
            if self.preData:
                self.enqueueData()
                return
            input_data = self.input.get_nowait()
        except QueueEmpty:
            time.sleep(QUEUE_EMPTY_SLEEP_TIME)
            return
        if not input_data.has_key('imageData') or not input_data['imageData']:
            down_start = time.time()
            image = download(input_data['ImageURL'])
            down_cost = round((time.time() - down_start) * 1000, 2)
            if image is None:
                increase(self.stats, 'down_get_false_total', self.threadId)
                logging.error('image download error. id: %s, url[%s], use time: %sms.' % (input_data['id'], input_data['ImageURL'], down_cost))
                return
            image_size = round(sys.getsizeof(image) / 1024, 2)
            if image_size <= 10:
                increase(self.stats, 'down_img_false_total', self.threadId)
                logging.error('image binary size[%sK] less than 10K, url[%s].' % (image_size, input_data['ImageURL']))
                return
            input_data['imageData'] = base64.b64encode(image)
            self.preData = input_data
            logging.info('image downloaded! id: %s, url: %s, down time: %sms, image size: %sK.' %
                         (input_data['id'], input_data['ImageURL'], down_cost, image_size))
