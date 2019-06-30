# coding:utf-8
# 本文件时间单位全为秒（s）
# 运行环境 0 开发 测试 1 生产
RUNNING_ENVIRON = 0
# oracle NLS连接设置
# select userenv('language') from dual;
ORACLE_NLS_LANG = 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK'

# 通过卡口文件生成卡口过滤条件字符串（in or not in）
# 在sql上过滤时卡口数量最好不要超过1000个
def _gettollgate():
    toll = []
    import os
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tollgate.rtf')
    with open(file_path, 'r') as fp:
        while True:
            line = fp.readline()
            if line:
                toll.append(line.strip())
            else:
                break
    # return "'" + "','".join(toll) + "'"
    return ','.join(toll)

TOLLGATE_IDS = _gettollgate()
# 卡口过滤使用 0 不过滤 1 在tollgate.rtf卡口列表的数据接入 2 与1相反
TOLL_FILTER_TYPE = 0

# mq一次消费数据条数
MQ_ONCE_COSUME_NUM = 50
# 自增时间间隔
READ_ONCE_WALK_TIME = 1*60
# reader连接重试时间（database）
READ_CONNECT_RETRY_TIME = 10
# 按id方式获取数据为空时sleep时间
READ_EMPTY_SLEEP_TIME = 10
# 按时间方式获取数据的保留时间
READ_RESERVE_TIME = 3*60
# 按时间方式获取某时间段数据为空时sleep时间
READ_RESERVE_SLEEP_TIME = 3*60

# 下载重试次数
HTTP_GET_RETRY_NUM = 2
# downloader下载图片的get时间
HTTP_GET_TIMEOUT = 10
# 上传重试次数
HTTP_POST_RETRY_NUM = 1
# writer上传过车信息的post时间
HTTP_POST_TIMEOUT = 10
# 下载上传出错重试前的sleep时间
HTTP_RETRY_SLEEP_TIME = 0.1

# 进程监控的轮询时间
PROC_MONITOR_ROTATE_TIME = 10
# 线程监控的轮询时间
THREAD_MONITOR_ROTATE_TIME = 5
# 程序记录间隔时间
POOL_ANCHOR_INTERVAL_TIME = 24 * 60 * 60

# 线程处理异常时再次运行前的sleep时间
THREAD_PROCESS_RETRY_TIME = 1
# queue为空时的sleep时间
QUEUE_EMPTY_SLEEP_TIME = 0.1

# pool stopping 轮询检测时间
POOL_STOP_CHECK_TIME = 2

# 日志最低记录级别1-DEBUG 2-INFO 3-WARNING 4-ERROR 5-CRITICAL
LOGGER_SET_LEVEL = 1
# debug日志rotate存留数
DEBUG_BACK_COUNT = 5
# info日志rotate存留数
INFO_BACK_COUNT = 1
# warning日志rotate存留数
WARNING_BACK_COUNT = 1
# error日志rotate存留数
ERROR_BACK_COUNT = 5
# critical日志rotate存留数
CRITICAL_BACK_COUNT = 1
# 单个日志文件大小（单位Bytes）
LOGGER_FILE_MAXBYTE = 500 * 1024 * 1024

if __name__ == '__main__':
    print TOLLGATE_IDS