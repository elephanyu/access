import os
import time
import logging
import traceback
import collections
from copy import deepcopy
from threading import Thread, Event
from multiprocessing import Queue, Manager

from seemmo.common.paths import script_path
from seemmo.common.utils import getReflectClass
from conf.globals import PROC_MONITOR_ROTATE_TIME, POOL_ANCHOR_INTERVAL_TIME

class ProcPool(Thread):
    def __init__(self, procs_setting):
        Thread.__init__(self)
        self.exit = Event()
        self.queues = {}
        self.procs_setting = procs_setting['procs']
        self.queues = {
            'input': Queue(procs_setting['read_queue_length']),
            'output': Queue(procs_setting['write_queue_length'])
        }
        self.stats = Manager().dict()
        order_key = [
            'read_success_total',
            'read_false_total',
            'down_success_total',
            'down_get_false_total',
            'down_img_false_total',
            'write_success_total',
            'write_post_false_total',
            'write_toll_false_total',
            'write_result_false_total',
            'read_speed',
            'down_speed',
            'write_speed',
            'read_queue_size',
            'write_queue_size'
        ]
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        if hasattr(collections, 'OrderedDict'):
            self.order_stats = collections.OrderedDict([
                ('start_time', now_time),
                ('last_anchor_time', now_time)
            ])
        else:
            self.order_stats = {
                'start_time': now_time,
                'last_anchor_time': now_time
            }
        for key in order_key:
            self.order_stats[key] = 0
        self.old_order_dict = deepcopy(self.order_stats)
        self.procs = []
        self.initialProcs()
        logging.info('proc_pool init.')

    def initialProcs(self):
        for i in range(len(self.procs_setting)):
            proc_setting = self.procs_setting[i]['proc']
            for j in range(proc_setting['proc_num']):
                self.procs.append(self.procFactory(proc_setting))

    def procFactory(self, proc_setting):
        module_path = 'seemmo.procs'
        proc_class = proc_setting['proc_class']
        proc = getReflectClass(module_path, proc_class)
        if not proc:
            logging.error("cannot find proc class %s" % (proc_class))
            import sys
            sys.exit()
        return proc(self.queues, proc_setting, self.stats)

    def startProcs(self):
        for proc in self.procs:
            proc.start()

    def stopProcs(self):
        # process stop in order
        for proc in self.procs:
            proc.stop()
            proc.join()

    def stop(self):
        self.exit.set()

    def get_stats(self):
        for k, v in self.order_stats.items():
            if 'total' in k:
                self.order_stats[k] = 0
        now_time = time.time()
        now_anchor = int(now_time/(POOL_ANCHOR_INTERVAL_TIME))
        last_anchor = int(time.mktime(time.strptime(self.order_stats['last_anchor_time'], '%Y-%m-%d %H:%M:%S'))/(POOL_ANCHOR_INTERVAL_TIME))

        if now_anchor != last_anchor or self.exit.is_set():
            for key, value in self.stats.items():
                if '-' in key:
                    clips = key.split('-')
                    orderKey = clips[0]
                    cflagKey = '%s.%s.%s' % (clips[0], clips[1], 'cflag')
                    if not self.stats[cflagKey]:
                        self.order_stats[orderKey] += value
                        self.stats[cflagKey] = True
            time_inteval = int(now_time - time.mktime(time.strptime(self.order_stats['last_anchor_time'], '%Y-%m-%d %H:%M:%S')))
            self.order_stats['read_speed'] = round(self.order_stats['read_success_total']/time_inteval, 1)
            self.order_stats['down_speed'] = round(self.order_stats['down_success_total']/time_inteval, 1)
            self.order_stats['write_speed'] = round(self.order_stats['write_success_total']/time_inteval, 1)
            start_time = self.order_stats['last_anchor_time']
            if now_anchor != last_anchor:
                # just for anchor change
                self.order_stats['last_anchor_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now_anchor * (POOL_ANCHOR_INTERVAL_TIME)))
            if self.exit.is_set():
                stop_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now_time))
            else:
                stop_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now_anchor * (POOL_ANCHOR_INTERVAL_TIME)))
            content = '[%s -- %s]' % (start_time, stop_time)
            try:
                for index in self.order_stats.keys():
                    if 'total' in index:
                        content = '%s\n%s=%s' % (content, index, self.order_stats[index])
                with open(os.path.join(script_path, 'conf', 'record.rtf'), 'a') as fp:
                    fp.write(content + '\n\n')
            except Exception:
                logging.error(traceback.format_exc())
        else:
            for key, value in self.stats.items():
                if '-' in key:
                    clips = key.split('-')
                    orderKey = clips[0]
                    cflagKey = '%s.%s.%s' % (clips[0], clips[1], 'cflag')
                    if not self.stats[cflagKey]:
                        self.order_stats[orderKey] += self.stats[key]
            self.order_stats['read_speed'] = round((self.order_stats['read_success_total'] - self.old_order_dict['read_success_total'])/PROC_MONITOR_ROTATE_TIME, 1)
            self.order_stats['down_speed'] = round((self.order_stats['down_success_total'] - self.old_order_dict['down_success_total'])/PROC_MONITOR_ROTATE_TIME, 1)
            self.order_stats['write_speed'] = round((self.order_stats['write_success_total'] - self.old_order_dict['write_success_total'])/PROC_MONITOR_ROTATE_TIME, 1)
        self.order_stats['read_queue_size'] = self.queues['input'].qsize()
        self.order_stats['write_queue_size'] = self.queues['output'].qsize()
        self.old_order_dict = deepcopy(self.order_stats)
        # logging.critical('stats info is: %s' % str(self.stats))
        logging.critical('main sumerize info is: %s' % str(self.order_stats))

    def monitor(self):
        for serial, proc in enumerate(self.procs):
            if not proc.is_alive():
                logging.error("%s is dead, setting is %s, relaunch now...." % (proc.name, str(proc.proc_setting)))
                self.procs[serial] = self.procFactory(proc.proc_setting)
                self.procs[serial].start()
        if not self.exit.is_set():
            self.get_stats()

    def run(self):
        self.startProcs()
        logging.info("procPool is running....")

        # monitor
        while not self.exit.is_set():
            try:
                time.sleep(PROC_MONITOR_ROTATE_TIME)
                self.monitor()
            except Exception:
                logging.error('exception in proc pool %s' % (traceback.format_exc()))
        logging.info("procpool is stopping")
        self.get_stats()
        self.stopProcs()
        logging.info("procpool is stopped")

