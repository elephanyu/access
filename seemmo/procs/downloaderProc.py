import time
import logging
from conf.globals import THREAD_MONITOR_ROTATE_TIME
from seemmo.procs.baseProc import BaseProc

class DownloaderProc(BaseProc):
    def __init__(self, queues, proc_setting, stats):
        BaseProc.__init__(self, queues, proc_setting, stats)
        logging.debug('%s init.' % (self.name))

    def threadFactory(self):
        class_name = self.proc_setting['threads']['thread_class']
        module_class = self.getClassByName(class_name)
        return module_class(self.input, self.output, proc_setting=self.proc_setting, stats=self.stats)

    def run(self):
        self.startThreads()

        # monitor server
        while not self.exit.is_set():
            time.sleep(THREAD_MONITOR_ROTATE_TIME)
            self.monitor()
        logging.debug("proc %s to stop" % (self.name))
        while True:
            if self.input.empty():
                self.stopThreads()
                break