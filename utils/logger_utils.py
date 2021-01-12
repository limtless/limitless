from project_setting import LOG_DIR,DEBUG
from configs.logging_settings import LogStateString
import logging
import os
import datetime
import json


def check_StateCode_ok(status_string):
    if status_string in LogStateString.__dict__.keys():
        return True
    else:
        return False

def get_debug_handle():
    # 设置输出日志格式
    f_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s[:%(lineno)d]-%(message)s")
    sh = logging.StreamHandler()  # 往屏幕上输出
    sh.setFormatter(f_formatter)
    return sh

def init_logger_handle(log_code,base_log_dir):
    ''' 初始化logger的读写handler '''
    current_date = str(datetime.datetime.now().strftime("%Y-%m-%d"))
    logdir = os.path.join(base_log_dir,current_date)
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    path_filename = os.path.join(logdir,log_code+".log")

    f_handler = logging.FileHandler(path_filename, encoding='utf-8')
    f_handler.setLevel(logging.INFO)

    # 设置输出日志格式
    f_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s[:%(lineno)d]-%(message)s")
    # 为handler指定输出格式
    f_handler.setFormatter(f_formatter)

    return f_handler

def get_logger(logcode):
    '''
    获取到相应logcode对应的logger对象
    '''
    logger = logging.getLogger(logcode)  # mylogger为日志器的名称标识，如果不提供该参数，默认为'root'

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)  # 设置logger处理等级
        logger.addHandler(init_logger_handle(logcode,LOG_DIR))

        if DEBUG:
            logger.addHandler(get_debug_handle())
    return logger



def savelog(logcode,msg = None,msg_dict=None):
    if not check_StateCode_ok(logcode):
        pass
    else:
        # logger = get_logger(logcode)
        # log_message = logcode + "#\n"
        # if msg:
        #     log_message += msg + "#\n"
        # if msg_dict:
        #     json_str = json.dumps(msg_dict, ensure_ascii=False,indent=4)
        #     log_message += json_str + "#"
        # logger.info(log_message)
        logger = get_logger(logcode)
        log_message = logcode + "#\n"
        if msg:
            log_message += msg + "#\n"
        if msg_dict:
            json_str = json.dumps(msg_dict, ensure_ascii=False,indent=4)
            log_message += json_str + "#"
        logger.info(log_message)