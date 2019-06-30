# coding=utf-8
import json
import urllib
import logging
import traceback
from collections import deque
from Queue import Full as QueueFull

import requests

from seemmo.threads.baseThread import BaseThread
from conf.mapping import data_mapping
from conf.globals import *
from seemmo.common.time import *
from seemmo.common.utils import increase
from seemmo.common.config import Config
from seemmo.business.huazunRegister import Register

class HuazunReaderTimeWalkThread(BaseThread):
    def __init__(self, output, proc_setting=None, stats=None):
        BaseThread.__init__(self, proc_setting=proc_setting, stats=stats)
        self.output = output
        self.preData = deque()
        self.repeatData = []
        self.config = Config('reader.cfg')
        self.current_time = self.config.get('current_time', now())
        self.current_startno = int(self.config.get('current_startno', 1))
        self.regist_stat = False
        self.now = self.config.get('now')

        logging.debug("Reader[%s] init." % (self.name))

    def register(self):
        register = Register(
            resturl=self.proc_setting['setting']['resturl'],
            username=self.proc_setting['setting']['username'],
            passwd=self.proc_setting['setting']['passwd'],
            identify=self.proc_setting['setting']['identify']
        )
        ret = register.register()
        if ret:
            self.regist_stat = True

    def keepalive(self, times=3):
        if times < 1:
            return False
        header = {
            'Content-Type': 'application/json;charset=UTF-8',
            'User-Identify': self.proc_setting['setting']['identify']
        }
        query_param = {
            'KeepaliveObject': {
                'DeviceID': self.proc_setting['setting']['identify']
            }
        }
        keepurl = self.proc_setting['setting']['resturl'] + '/VIID/System/Keepalive'
        session = requests.Session()
        try:
            response = session.get(url=keepurl, headers=header, data=json.dumps(query_param))
            if response.status_code == 200:
                res_data = json.loads(response.content)
                if res_data.has_key('ResponseStatusObject') and res_data['ResponseStatusObject']['StatusCode'] == 0:
                    logging.debug('keepalive success')
                    return True
                else:
                    res_data = json.loads(response.content)
                    logging.error('access register url result: %s' % res_data['ResponseStatusObject']['StatusString'])
                    return self.keepalive(times=times-1)
            else:
                logging.error('access register url http err: %s' % response.status_code)
                return self.keepalive(times=times-1)
        except Exception:
            logging.error(traceback.format_exc())

    def enqueueData(self):
        one = self.preData.popleft()
        try:
            self.output.put(one, block=False)
            logging.info('enqueue new data: %s, %s' % (one['id'], one['ImageURL']))
            increase(self.stats, 'read_success_total', self.threadId)
        except QueueFull:
            self.preData.appendleft(one)
            return

    def process(self):
        if self.preData:
            self.enqueueData()
            return
        if not self.regist_stat:
            self.register()
            return
        self.now = now()
        next_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.mktime(time.strptime(self.current_time, '%Y-%m-%d %H:%M:%S')) + READ_ONCE_WALK_TIME))
        if seconds_between(next_time, self.now) <= READ_RESERVE_TIME:
            time.sleep(READ_RESERVE_SLEEP_TIME)
            return
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'User-Identify': self.proc_setting['setting']['identify']
        }
        query_param = '''/VIID/MotorVehicles?RecordStartNo=%s&PageRecordNum=%s&(MotorVehicle.CreateTime BETWEEN '%s' and '%s')&(Sort = MotorVehicle.CreateTime)''' % (self.current_startno, self.proc_setting['setting']['pagesize'], self.current_time, next_time)
        query_url = self.proc_setting['setting']['resturl'] + query_param.replace(' ', '%20')
        session = requests.Session()
        try:
            response = session.get(url=query_url, headers=headers)
            if response and response.status_code == 200:
                res_data = json.loads(response.content)
                if isinstance(res_data, dict):
                    if res_data.has_key('ResponseStatusObject') and res_data['ResponseStatusObject']['StatusCode'] == 4:
                        self.regist_stat = False
                        return
                    else:
                        logging.error('huazun rest api err, please call data_aceess_addmin')
                        logging.error(response.content)
                        return
                else:
                    if self.current_startno <= res_data[0]['MotorVehiclesListObject']['Pages']:
                        logging.info('result.size: %s, StartDateTime: %s, RecordStartNo: %s' % (res_data[0]['MotorVehiclesListObject']['PageRecordNum'], self.current_time, self.current_startno))
                        logging.debug('RecordStartNo:%s,PageRecordNum:%s,MaxNumRecordReturn:%s,Offset:%s,Pages:%s' % (
                            res_data[0]['MotorVehiclesListObject']['RecordStartNo'],
                            res_data[0]['MotorVehiclesListObject']['PageRecordNum'],
                            res_data[0]['MotorVehiclesListObject']['MaxNumRecordReturn'],
                            res_data[0]['MotorVehiclesListObject']['Offset'],
                            res_data[0]['MotorVehiclesListObject']['Pages']
                        ))
                        for row in res_data[0]['MotorVehiclesListObject']['MotorVehiclesObject']:
                            data = data_mapping(row)
                            if data['ImageURL'] is None:
                                increase(self.stats, 'read_false_total', self.threadId)
                                # logging.error('Data image url error: %s' % str(row))
                                continue
                            if data['deviceId'] is None:
                                increase(self.stats, 'read_false_total', self.threadId)
                                # logging.error('Data image url error: %s' % str(row))
                                continue
                            if TOLL_FILTER_TYPE == 1:
                                if data['deviceId'] not in TOLLGATE_IDS:
                                    continue
                            elif TOLL_FILTER_TYPE == 2:
                                if data['deviceId'] in TOLLGATE_IDS:
                                    continue
                            self.preData.append(data)
                        self.current_startno += 1
                    else:
                        self.current_startno = 1
                        self.current_time = next_time
            else:
                logging.error('exception occurs when access rest api, url: %s, rest api may stopped!' % query_url)
        except Exception:
            logging.error('exception occurs when access rest api, url: \n%s, err: %s' % (query_url, traceback.format_exc()))
            return

        try:
            self.config.set('current_time', self.current_time)
            self.config.set('current_startno', self.current_startno)
            self.config.set('now', self.now)
            self.config.save()

        except Exception as e:
            logging.error("Failed to update config file %s: %s." % (self.config.filepath, e))
            self.current_time = self.config.get('current_time', now())
            self.current_startno = self.config.get('current_startno', 1)
            self.now = self.config.get('now')


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
                    # logging.info('wait thread reader\'s predata to process, predata len : %s' % len(self.preData))
                    self.enqueueData()
                else:
                    break
        logging.debug('thread is stopped %s' % (self.name))
