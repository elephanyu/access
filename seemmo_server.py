import time
import signal
import logging
from conf import settings
from seemmo.common.default import *
from conf.globals import POOL_STOP_CHECK_TIME
from seemmo.procs.procPool import ProcPool

__author__ = 'huhuan, fuxiangyu, wct'

procpool = None
def quit(signum, frame):
    global procpool
    if procpool is not None and procpool.is_alive():
        logging.info('main begin to stop')
        procpool.stop()

def main():
    global procpool
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    procpool = ProcPool(settings.PROC_SETTING)
    logging.info('main init')
    procpool.start()
    signal.signal(signal.SIGTERM, quit)
    while procpool.is_alive():
        time.sleep(POOL_STOP_CHECK_TIME)
    logging.info('main stopped')

if __name__ == '__main__':
    main()
