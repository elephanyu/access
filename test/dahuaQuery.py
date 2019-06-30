# coding:utf-8
import os
import sys
import time
import json
import traceback
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'conf'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'packages'))

import requests

from settings import PROC_SETTING

if __name__ == '__main__':
    # update this set in real environ
    authcode = PROC_SETTING['procs'][0]['proc']['setting']['authcode']
    pagesize = PROC_SETTING['procs'][0]['proc']['setting']['pagesize']
    resturl = PROC_SETTING['procs'][0]['proc']['setting']['resturl']
    query_time = '2018-4-5 10:00:00'
    time_interval = 30
    next_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.mktime(time.strptime(query_time, '%Y-%m-%d %H:%M:%S')) + time_interval))
    current_index = 1000
    next_index = current_index + pagesize
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': authcode
    }
    query_data = {
        # 'startDate': current_time,
        # 'endDate': next_time,
        'startId': current_index,
        'endId': next_index,
        'page': {
            'pageNo': 1,
            'pageSize': pagesize
        }
    }
    query_url = resturl + '?q=%s' % (json.dumps(query_data))
    session = requests.Session()
    try:
        response = session.get(url=query_url, headers=headers)
        if response and response.status_code == 200:
            res_data = json.loads(response.content)
            if res_data['code'] == 100:
                rows = res_data['data']['rows']
                print('result.size: %s, startId: %s.' % (rows and len(rows), current_index))
                print('result.size: %s, startTime: %s.' % (rows and len(rows), current_time))
                if rows is not None and len(rows) > 0:
                    print 'result data:\n'
                    for row in rows:
                        print row
                else:
                    print 'please update current_time in this file!!!'
            else:
                print('exception occurs when access rest api, url: %s, response err: %s' % (query_url, res_data['msg']))
        else:
            print('exception occurs when access rest api, url: %s, rest api may stopped!' % query_url)
    except Exception:
        print('exception occurs when access rest api, url: \n%s, err: %s' % (query_url, traceback.format_exc()))
