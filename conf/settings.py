# coding=utf-8
PROJECT = '地名'

PROC_SETTING = {'procs':[
    # {'proc': {'proc_class': 'ReaderProc', 'proc_num': 1, 'threads': {'thread_class': 'MReaderIThread', 'thread_num': 1},
    #           'setting': {'ip': '192.168.2.157', 'port': 3306, 'user': 'emp', 'password': '123456','dbname': 'employees',
    #                       'query_temp': 'select id, kkid, gcsj, url from gcxx where id > %s order by id limit 50'},
    #           }},
    {'proc':{'proc_class':'ReaderProc','proc_num':2,'threads':{'thread_class':'RReaderThread','thread_num': 2},
                    'setting':{'ip':'10.10.4.48','port':5672,'user':'admin','password':'admin','vhost':'nvhost','que_name':'nvque'},
                   }},
    {'proc':{'proc_class':'DownloaderProc','proc_num':2,'threads':{'thread_class':'DownloaderThread','thread_num': 10},
                   }},
    {'proc':{'proc_class':'WriterProc','proc_num':2,'threads':{'thread_class':'WriterThread','thread_num': 2},
                    'setting':{'service_url':'http://192.168.2.29:8088/client/vehiclelogic.php'},
                   }},
    ],
    'read_queue_length':100, 'write_queue_length':20}



'''
PROC_SETTING
    |----procs          进程数组
    |      |------proc  进程
    |               |-------proc_class    进程类名，对应python类(ReaderProc, DownloaderProc, WriterProc)
    |               |-------proc_num      进程个数
    |               |-------setting       进程私有配置，主要用于此进程需要的配置,会传给进程中的每个线程
    |               |-------threads       进程中的线程配置
    |                          |------thread_class  线程类名，对应python类，文件名为类名首字母小写
    |                                               默认加载模块路径seemmo.{location}.thread_class模块
    |                          |------thread_num    线程个数
    |
    |----read_queue_length   读数据队列长度
    |----write_queue_length  写数据队列长度
    |----location            接入地名
'''

