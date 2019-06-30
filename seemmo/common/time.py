from __future__ import absolute_import
import time

default_format = '%Y-%m-%d %H:%M:%S'
seconds_per_day = 24 * 3600

def seconds_between(fromstring, tostring):
    return abs((to_mstimestamp(fromstring) - to_mstimestamp(tostring))) / 1000

def future(string, minute=1, second=0):
    return to_string(to_mstimestamp(string) + minute * 60 * 1000 + second * 1000)

def now(format='%Y-%m-%d %H:%M:%S'):
    return time.strftime(format, time.localtime(time.time()))

def ms_now():
    return int(time.time() * 1000)

def mseconds_between(inttime1, inttime2):
    return abs(inttime1 - inttime2)

def to_string(mstimestamp, format=default_format):
    return time.strftime(format, time.localtime(int(mstimestamp) / 1000))

def to_mstimestamp(string, format=default_format):
    return int(time.mktime(time.strptime(string, format))) * 1000

def str2timestamp(string, format=default_format):
    return int(time.mktime(time.strptime(string, format)))

def timestamp2str(timestamp, format=default_format):
    return time.strftime(format, time.localtime(int(timestamp)))

def today(format='%Y-%m-%d'):
    return timestamp2str(time.time(), format)

def day_offset(day_str=today(), offset=1, format=default_format):
    return timestamp2str(str2timestamp(day_str, format) + seconds_per_day * offset, format)

