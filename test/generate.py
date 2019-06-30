# coding:utf-8
import os
import sys
import time
import random
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

def test_data(lasttime):
    data = [
        {
            'sbbh': '10101011',
            'picurl': 'http://10.10.29.67/dir/1.jpeg',
            'cphm': '0'
        },
        {
            'sbbh': '10101012',
            'picurl': 'http://10.10.29.67/dir/2.jpg',
            'cphm': '鲁QK9999'
        },
        {
            'sbbh': '10101013',
            'picurl': 'http://10.10.29.67/dir/三.jpeg',
            'cphm': '鲁HH9999'
        },
        {
            'sbbh': '10101014',
            'picurl': 'http://10.10.29.67/dir/四.jpeg',
            'cphm': '苏D3Q520'
        }
    ]
    choice = random.choice(data)
    ini = random.randint(1,10)
    if ini <= 7:
        choice['gcsj'] = lasttime + 1
    else:
        choice['gcsj'] = lasttime - 1

if __name__ == '__main__':
    setting = PROC_SETTING['procs'][0]['proc']['setting']
    db_user = setting['user']
    db_passwd = setting['password']
    db_host = setting['ip']
    db_port = setting['port']
    db_name = setting['dbname']

    ncon = get_connection(user=db_user, passwd=db_passwd, host=db_host, port=db_port, dbnm=db_name)
    sql_temp = '''insert into pass_info (sbbh,gcsj,picurl,cphm) values(%s,'%s','%s','%s')'''

    lasttime = int(time.time())
    for i in xrange(100000):
        data = test_data(lasttime)
        sql = sql_temp % (
            data['sbbh'],
            time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(data['gcsj'])),
            data['picurl'],
            data['cphm']
        )
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
        lasttime = data['lasttime']

