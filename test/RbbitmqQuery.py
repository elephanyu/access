# coding:utf-8
import os
import sys
import time
import json
import traceback
from collections import deque
from threading import Thread
from multiprocessing import Event
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'packages'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'conf'))

import pika

from settings import PROC_SETTING

class Cosumer(Thread):
    def __init__(self):
        Thread.__init__(self)
        setting = PROC_SETTING['procs'][0]['proc']['setting']
        self.user = setting['user']
        self.passwd = setting['password']
        self.host = setting['ip']
        self.port = setting['port']
        self.vhost = setting['vhost']
        self.queue = setting['que_name']
        self.input = deque()
        self.exit = Event()

    def stop(self):
        self.exit.set()

    def endata(self):
        try:
            data = self.input.popleft()
            print(data)
        except Exception:
            print traceback.format_exc()

    def connection(self):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.vhost,
                credentials=pika.PlainCredentials(self.user, self.passwd),
                channel_max=10,
                frame_max=10000,
                blocked_connection_timeout=5*60
            ))
            return connection
        except Exception:
            print(traceback.format_exc())
            return None

    def cosumemany(self):
        connection = self.connection()
        if connection != None:
            try:
                channel = connection.channel()
                channel.queue_declare(queue=self.queue, passive=True)
                while True:
                    method, properties, body = channel.basic_get(self.queue)
                    if method is None:
                        connection.close()
                        time.sleep(2)
                        break
                    self.input.append(json.loads(body))
                    channel.basic_ack(method.delivery_tag)
                    if method.delivery_tag == 10:
                        connection.close()
                        # self.stop()
                        break
            except Exception:
                print(traceback.format_exc())


    def run(self):
        while not self.exit.is_set():
            try:
                if self.input:
                    self.endata()
                    continue
                self.cosumemany()
            except Exception:
                raise traceback.format_exc()


if __name__ == '__main__':
    cosume = Cosumer()
    cosume.start()