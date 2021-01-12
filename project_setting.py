import os
# 项目根目录地址
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# 关键词存储目录
KEYWORDS_DATA_PATH = os.path.join(PROJECT_ROOT,"regular_matching_rules/keywords")
KEYWORDS_EXTEND_DATA_PATH = os.path.join(PROJECT_ROOT,'regular_matching_rules/extend_keywords')
# 日志存储目录
LOG_DIR = os.path.join(PROJECT_ROOT,'log_files')

# 确认了有问题的网页url存储地址
NO_NEED_CHECK_URL_DIR = os.path.join(PROJECT_ROOT,'regular_matching_rules/no_need_check')

#是否是debug模式检测
DEBUG = os.environ.get("info_extract_debug",1)

if DEBUG:
    MongoUrl = "mongodb://localhost:27017"
else:
    MongoUrl = "mongodb://192.168.2.181:27017"