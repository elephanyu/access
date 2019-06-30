# coding:utf-8
import logging
import traceback

from seemmo.common.coding import tran2UTF8

def data_mapping(row):
    return {
        'cmd': 'addinfo',
        'magic': 'hfrz',
        'id': row[0],
        'deviceId': row[1],
        'snapshotTime': time_mapping(row[2]),
        'ImageURL': url_mapping(row[3]) if row[3] and row[3] != '0' else None,
        'plateNumber': tran2UTF8(row[4]) if row[4] and row[4] != '0' else '',
    }

def url_mapping(url):
    # all to str and in utf-8
    if url[:3] == 'ftp':
        return url
    else:
        return tran2UTF8(url)

    # type one
    # return 'http://10.102.167.17:82' + url

def time_mapping(sql_datetime):
    import time
    return int(time.mktime(time.strptime(sql_datetime, '%Y-%m-%d %H:%M:%S'))) * 1000
    # return int(time.mktime(sql_datetime.timetuple()) * 1000) + int(sql_datetime.microsecond / 1000)

'''
参数	            值	     必须  说明
magic	        hfrz	 是	   校检参数，传hfrz
cmd	            addinfo	 是	   处理类型：数据接入
snapshotTime	-	     是	   unix毫秒时间戳，例如“1490409584000”
deviceId	    -	     是	   数据来源方的卡口编号，例如“10445600”
direction	    -	     否	   可选参数,如果同一个设备多个方向就传,否则不传本参数
imageData	    -	     是	   base64编码后的图片
ImageURL	    -	     否	   图片url，没有可不传
fileName	    -	     否	   可选参数，如果是不会重复的文件名，就传，否则不传本参数
plateNumber	    -	     否	   一次识别号牌号码，没有就不传
plateType	    -	     否	   一次识别号牌类型，没有就不传
'''
