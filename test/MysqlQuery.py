# coding:utf-8
import os
import sys
import time
import traceback
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'conf'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'packages'))

import MySQLdb

from settings import PROC_SETTING

def get_connection(user='', passwd='', host='', port=1521, dbnm='ORCL'):
    try:
        # update set by real environ
        connection = MySQLdb.connect(
                host=host,
                port=port,
                user=user,
                passwd=passwd,
                db=dbnm,
                charset='utf8',
                connect_timeout=10
            )
        return connection
    except Exception:
        print('database connect err:\n%s' % traceback.format_exc())
        return None

if __name__ == '__main__':
    setting = PROC_SETTING['procs'][0]['proc']['setting']
    db_user = setting['user']
    db_passwd = setting['password']
    db_host = setting['ip']
    db_port = setting['port']
    db_name = setting['dbname']
    time_interval = 30
    query_time = '2018-04-04 10:00:00'
    next_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.mktime(time.strptime(query_time, '%Y-%m-%d %H:%M:%S')) + time_interval))
    query_index = 10000
    # sql = '''SELECT * FROM TABLE_NAME/VIEW_NAME WHERE ID>%s ORDER BY ID LIMIT 100''' % query_index
    sql = '''SELECT * FROM TABLE_NAME/VIEW_NAME WHERE GCSJ between TO_DATE('%s','yyyy-mm-dd hh24:mi:ss') AND TO_DATE('%s','yyyy-mm-dd hh24:mi:ss') ORDER BY ID''' % (query_time, next_time)
    ncon = get_connection(user=db_user, passwd=db_passwd, host=db_host, port=db_port, dbnm=db_name)
    if ncon is not None:
        try:
            cursor = ncon.cursor()
            cursor.execute(sql)
            ret = cursor.fetchmany(5)
            desc = cursor.description
            print 'table or view description is:\n%s' % desc
            print '\n\nquery result:'
            for row in ret:
                print row
        except Exception as e:
            print('sql: %s,\nerror: %s' % (sql, e))

