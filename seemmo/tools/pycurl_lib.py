# coding:utf-8
import time
import json
import pycurl
import logging
import traceback
import StringIO
from conf.globals import HTTP_GET_TIMEOUT, HTTP_GET_RETRY_NUM, HTTP_POST_TIMEOUT, HTTP_POST_RETRY_NUM, HTTP_RETRY_SLEEP_TIME

from seemmo.common.coding import tran2UTF8

def getclient(method='get'):
    c = pycurl.Curl()
    c.setopt(pycurl.NOPROGRESS, 1)
    c.setopt(pycurl.MAXREDIRS, 2)
    c.setopt(pycurl.NOSIGNAL, 1)
    c.setopt(pycurl.FORBID_REUSE, 1)
    c.setopt(pycurl.FRESH_CONNECT, 1)
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    if method == 'get':
        c.setopt(pycurl.CONNECTTIMEOUT, 3)
        c.setopt(pycurl.TIMEOUT, HTTP_GET_TIMEOUT)
    elif method == 'post':
        c.setopt(pycurl.CONNECTTIMEOUT, 3)
        c.setopt(pycurl.TIMEOUT, HTTP_POST_TIMEOUT)
    else:
        logging.error('err method for pycurl: %s' % method)
        return None
    return c

def download(url):
    url = tran2UTF8(url)
    lasterr = ''
    for i in range(HTTP_GET_RETRY_NUM):
        try:
            c = getclient()
            if c is not None:
                buf = StringIO.StringIO()
                c.setopt(pycurl.WRITEFUNCTION, buf.write)
                # pycurl url is in str method otherwise unicode
                c.setopt(pycurl.URL, url.encode('utf-8'))
                c.perform()
                status_code = c.getinfo(pycurl.HTTP_CODE)
                if status_code == 200:
                    ret = buf.getvalue()
                    # debug reserve code
                    # logging.debug('down time total: %sms, connect: %sms, pretran: %sms' % (
                    #     round(c.getinfo(pycurl.TOTAL_TIME)*1000, 2),
                    #     round(c.getinfo(pycurl.CONNECT_TIME)*1000, 2),
                    #     round(c.getinfo(pycurl.PRETRANSFER_TIME)*1000, 2),
                    # ))
                    # round(c.getinfo(pycurl.REDIRECT_TIME)*1000, 2)
                    return ret
                else:
                    lasterr = 'status code %s' % c.getinfo(pycurl.HTTP_CODE)
                c.close()
                buf.close()
            else:
                lasterr = 'pycurl client get false'
        except Exception:
            lasterr = traceback.format_exc()
            time.sleep(HTTP_RETRY_SLEEP_TIME)

    logging.error('exception occurs when get url[%s]. [%s]' % (url, lasterr))
    return None

def post(url, param):
    url = tran2UTF8(url)
    param_json = param and json.dumps(param)
    header = ['Content-Type:application/json']
    lasterr = ''
    for i in range(HTTP_POST_RETRY_NUM):
        try:
            c = getclient(method='post')
            if c is not None:
                buf = StringIO.StringIO()
                c.setopt(pycurl.HTTPHEADER, header)
                c.setopt(pycurl.POSTFIELDS, param_json)
                c.setopt(pycurl.WRITEFUNCTION, buf.write)
                c.setopt(pycurl.URL, url)
                c.perform()
                status_code = c.getinfo(pycurl.HTTP_CODE)
                if status_code == 200:
                    ret = buf.getvalue()
                    return ret
                else:
                    lasterr = 'status code %s' % c.getinfo(pycurl.HTTP_CODE)
                c.close()
                buf.close()
            else:
                lasterr = 'pycurl client get false'
        except Exception:
            lasterr = traceback.format_exc()
            time.sleep(HTTP_POST_RETRY_NUM)

    if param and param.has_key('imageData'):
        del param['imageData']
        logging.error('exception occurs when post url[%s], param[%s]. [%s]' % (url, json.dumps(param), lasterr))
    else:
        logging.error('exception occurs when post url[%s], param[%s]. [%s]' % (url, param_json, lasterr))
    return None


'''
pycurl说明：
#连接的等待时间，设置为0则不等待
c.setopt(pycurl.CONNECTTIMEOUT, 5)      
#请求超时时间
c.setopt(pycurl.TIMEOUT, 5)             
#是否屏蔽下载进度条，非0则屏蔽
c.setopt(pycurl.NOPROGRESS, 0)          
#指定HTTP重定向的最大数
c.setopt(pycurl.MAXREDIRS, 5)           
#完成交互后强制断开连接，不重用
c.setopt(pycurl.FORBID_REUSE, 1)      
#强制获取新的连接，即替代缓存中的连接
c.setopt(pycurl.FRESH_CONNECT,1)        
#设置保存DNS信息的时间，默认为120秒
c.setopt(pycurl.DNS_CACHE_TIMEOUT,60)   
#指定请求的URL
c.setopt(pycurl.URL,"http://www.baidu.com")        
#配置请求HTTP头的User-Agent
c.setopt(pycurl.USERAGENT,"Mozilla/5.2 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50324)")    
#将返回的HTTP HEADER定向到回调函数getheader
c.setopt(pycurl.HEADERFUNCTION, getheader)
# 指定post数据  
curl.setopt(pycurl.POSTFIELDS, data) 
#将返回的内容定向到回调函数getbody
c.setopt(pycurl.WRITEFUNCTION, getbody)      
#将返回的HTTP HEADER定向到fileobj文件对象
c.setopt(pycurl.WRITEHEADER, fileobj)        
#将返回的HTML内容定向到fileobj文件对象
c.setopt(pycurl.WRITEDATA, fileobj)

#返回的HTTP状态码
c.getinfo(pycurl.HTTP_CODE)         
#传输结束所消耗的总时间
c.getinfo(pycurl.TOTAL_TIME)        
#DNS解析所消耗的时间
c.getinfo(pycurl.NAMELOOKUP_TIME)   
#建立连接所消耗的时间
c.getinfo(pycurl.CONNECT_TIME)      
#从建立连接到准备传输所消耗的时间
c.getinfo(pycurl.PRETRANSFER_TIME)  
#从建立连接到传输开始消耗的时间
c.getinfo(pycurl.STARTTRANSFER_TIME)    
#重定向所消耗的时间
c.getinfo(pycurl.REDIRECT_TIME)     
#上传数据包大小
c.getinfo(pycurl.SIZE_UPLOAD)       
#下载数据包大小
c.getinfo(pycurl.SIZE_DOWNLOAD)      
#平均下载速度
c.getinfo(pycurl.SPEED_DOWNLOAD)    
#平均上传速度
c.getinfo(pycurl.SPEED_UPLOAD)      
'''