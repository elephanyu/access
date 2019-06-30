import time
import logging
import traceback
from threading import Thread, Event
from conf.globals import THREAD_PROCESS_RETRY_TIME

__author__ = 'wct'

class BaseThread(Thread):
    def __init__(self, proc_setting=None, stats=None):
        Thread.__init__(self)
        self.proc_setting = proc_setting
        self.stats = stats
        self.exit = Event()
        self.threadId = self.name.split('-')[1]

    def stop(self):
        self.exit.set()

    def process(self):
        pass

    def run(self):
        # import ctypes
        # self.threadId = ctypes.CDLL('libc.so.6').syscall(186)
        logging.debug('thread is starting %s' % (self.name))
        while not self.exit.is_set():
            try:
                self.process()
            except Exception:
                logging.error('exception occurs when get data! %s' % (traceback.format_exc()))
                time.sleep(THREAD_PROCESS_RETRY_TIME)
        logging.debug('thread is stopped %s' % (self.name))

