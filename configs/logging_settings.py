class LogStateString():
    FatalError = "FatalError"  # 代码异常,一般都是致命错误
    FatalError_OutputJson_CheckFailed = "FatalError_OutputJson_CheckFailed"  # 输出json检查失败
    FatalError_LockKeyWords = "FatalError_LockKeyWords"
    FatalError_TypeNotList = "FatalError_TypeNotList"

    Warning_ContentLen0 = "Warning_ContentLen0"  # 字段内容空
    Warning_KeyNotSuitable = "Warning_KeyNotSuitable"  # 在状态机解析过程中，key出现在了不应该出现的parseMode里面
    Waring_WeiZhiKeyWords = "Waring_WeiZhiKeyWords"  # 有未知字段
    Waring_ContentLenMoreThan100 = "Waring_ContentLenMoreThan100"  # 字段内容超過100

    Info_NormalRecord = 'Info_NormalRecord'  # zhangxing 正常记录所需查看信息
    Info_KafkaMessage = "Info_KafkaMessage"  # add by qiufengfeng ,save kafka message dict
