import logging
from multiprocessing import Process, Event, Manager

from conf import settings
from seemmo.common.utils import getReflectClass

class BaseProc(Process):
    def __init__(self, queues, proc_setting, stats):
        Process.__init__(self)
        self.exit = Event()
        self.input = queues['input'] if queues.has_key('input') else None
        self.output = queues['output'] if queues.has_key('output') else None
        self.proc_setting = proc_setting
        # self.stats = Manager().dict()
        self.stats = stats
        self.threads = []
        self.initialThreads()

    def initialThreads(self):
        for i in range(self.proc_setting['threads']['thread_num']):
            self.threads.append(self.threadFactory())

    def threadFactory(self):
        pass

    def getClassByName(self, class_name):
        module_path = 'seemmo.threads'
        module_class = getReflectClass(module_path, class_name)
        if not module_class:
            import sys
            logging.error("cannot find proc class %s" % (class_name))
            sys.exit()
        return module_class

    def startThreads(self):
        for thread in self.threads:
            thread.start()

    def stopThreads(self):
        for thread in self.threads:
            thread.stop()
        for thread in self.threads:
            thread.join()
        if self.input:
            self.input.cancel_join_thread()
        if self.output:
            self.output.cancel_join_thread()
        logging.info("proc %s is stopped" % (self.name))

    def stop(self):
        self.exit.set()

    def monitor(self):
        for serial, thread in enumerate(self.threads):
            if not thread.isAlive():
                logging.error("%s is dead, thread setting is %s, relaunch now...." % (thread.name, str(thread.proc_setting)))
                self.threads[serial] = self.threadFactory()
                self.threads[serial].start()

    def run(self):
        pass
