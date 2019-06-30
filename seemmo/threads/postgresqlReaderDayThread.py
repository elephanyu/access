# coding=utf-8
import logging
import threading
import Queue
import time

from seemmo.tools.config import Config
from datasource import DataSource
from seemmo.tools.time import today, day_offset, now, str2timestamp

__author__ = 'huhuan'

ERROR = -1
OK = 0
EMPTY = 1
RESERVED = 2

LIMIT = 100


class DailyReader(threading.Thread):
    def __init__(self,
                 day=today('%Y_%m_%d'),
                 settings=__import__('settings', level=0),
                 mapping=__import__('mapping', level=0),
                 output=Queue.Queue()):
        threading.Thread.__init__(self)

        self.day = day

        self.settings = settings
        self.mapping = mapping

        self.output = output

        self.datasource = DataSource(settings)
        self.config = Config('reader-%s.cfg' % day)

        self.deadline = str2timestamp(day_offset(day_str=self.day, offset=7, format='%Y_%m_%d'), format='%Y_%m_%d')

        self.stopped = False

        self.current_index = int(self.config.get('current_index', 0))
        self.now = self.config.get('now')

        logging.info("Reader-%s init done!" % self.day)

    def dead(self):
        return time.time() > self.deadline

    def clean(self):
        self.config.clean()
        return True

    def stop(self):
        self.stopped = True

    def process(self):
        self.now = now()

        execute_sql = self.settings.QUERY_SQL_TEMPLATE % (self.day, self.current_index)

        rows = self.datasource.query_list(execute_sql)

        if rows is not None and len(rows) != 0:
            logging.info('result.size: %d <== sql: %s' % (len(rows), execute_sql))

            for row in rows:
                data = self.mapping.data_mapping(row)

                if data['id'] > self.current_index:
                    self.current_index = data['id']

                self.output.put(data, block=True)
                logging.info('enqueue new data: %s, %s' % (data['id'], data['ImageURL']))

        try:
            self.config.set('current_index', str(self.current_index))
            self.config.set('now', self.now)
            self.config.save()

        except Exception as e:
            logging.debug("Failed to update config file %s: %s." % (self.config.filepath, e))
            return ERROR

        if rows is None or len(rows) == 0:
            return EMPTY
        else:
            return OK

    def run(self):
        try:
            while True:
                if self.stopped or (self.dead() and self.clean()):
                    break

                result = self.process()
                if result == RESERVED or result == EMPTY:
                    time.sleep(5)
                    continue

        except Exception as e:
            logging.error('exception occurs when read data! %s' % e)


