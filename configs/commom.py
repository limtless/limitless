class FlagUtil:
    """
    一些字关联字段预定义
    ADD:表示可以通过ADD前后两者相加得到了前者
    FROM:表示可通过FROM后的名称查找FROM前者
    SUBSTRACT:表示可通过subtract前者前后者得到前者
    """
    PROJECT_NAME_ADD_BID_SECTION_NAME = "PROJECT_NAME_ADD_BID_SECTION_NAME"  # 项目名称=项目名称+标段名称（标段名称缺失）
    PROJECT_NAME_FROM_BID_SECTION_NUM = 'PROJECT_NAME_FROM_BID_SECTION_NUM'  # 项目名称缺失，可以通过标段编号查询

########################### 公告类型相关定义 #################################
class PageType():
    BID_ANNOUNCEMENT = "招标公告"  # 招标公告
    BIDDING_ANNOUNCEMEN = "投标公告"  # 投标公告
    WIN_BIDDING_ANNOUNCEMENT = "中标公告"  # 中标公告


def get_pagetype(text):
    page_type = None
    if '招标公告' in text:
        page_type = PageType.BID_ANNOUNCEMENT
    elif '中标公告' in text:
        page_type = PageType.WIN_BIDDING_ANNOUNCEMENT
    elif '投标公告' in text:
        page_type = PageType.BIDDING_ANNOUNCEMEN
    return page_type


########################### 数据库相关定义 #################################
db_table_list = [
    "工程公告信息",
    "工程基本信息",
    "工程招标信息",
    '工程投标信息',
]


class DBTableInfo(object):
    '''
    工程相关数据库表明定义
    '''
    PROJECT = "工程基本信息"  # 工程基本信息
    PROJECT_ANNOUNCEMENT = "工程公告信息"  # 工程公告信息
    PROJECT_BID_INFORMATION = "工程招标信息"  # 工程招标信息
    PROJECT_WIN_BIDDING_INFORMATION = "工程投标信息"  # 工程投标信息
    UNKNOW = "未知"
    IGNORE ="忽略"


########################### 提取信息过程中状态相关定义 #################################
class PageParseMode():
    '''解析过程中的状态'''
    BIDDER_INFO = "招标人信息"  # 招标人相关信息
    BIDDER_AGENCY_INFO = "招标代理机构"  # 招标代理人相关信息


mode_priority = {
    '工程基本信息': 10,
    '工程招标信息': 9,
    "工程投标信息": 6,
}

mode_to_table = {
    "招标人和招标代理机构": "工程招标信息",
    "招标人信息": '工程招标信息',
    "招标代理机构": '工程招标信息',
    "工程基本信息": '工程基本信息',
    "工程公告信息": '工程公告信息',
    "中标信息": "工程投标信息",
    '未知': "未知",
    "忽略":"忽略",
}

# 判断是否需要存为list结构
mutiply_keys = [
    '地址',
    '电话',
    '名称',
    '联系人',
    '邮箱',
    '邮编',
    '传真',
    '官网地址'
]
list_key = ['招标人信息' + key for key in mutiply_keys]
list_key.extend(['招标代理机构' + key for key in mutiply_keys])
#list_key.append("中标信息联系人")  # add by zhangxing/存在多个中标信息联系人情况，这里记为list/(http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20200520/87b07379-dad3-4d67-9e74-6f5a23ae202f.html)
#list_key.extend(["未知联系人","未知传真","未知电话"])
list_key.extend(['未知' + key for key in mutiply_keys])
notice_style_zhongbiao = [
                          "中标公告",
                          "中标结果公示",
                          "中标结果公告",
                          "成交公告"
]
notice_style_zhaobiao = [
                        "招标公告",
                        "招标公告/资审公告",
                        "邀请招标公告",
                        "公开招标公告",
]

notice_style_dic = {
                          "中标公告": "中标公告",
                          "中标结果公示": "中标公告",
                          "中标结果公告": "中标公告",
                          "成交公告": "中标公告",
                          "招标公告": "招标公告",
                          "招标公告/资审公告": "招标公告",
                          "邀请招标公告": "招标公告",
                          "公开招标公告": "招标公告",
}

replaceinfo_dict_zhaobiao={"工程招标信息":  # 未知前转为后
                                    {
                                      '未知工期': "标段工期",
                                      # '未知项目负责人资质等级': "标段投标人资质类别要求",


                                      "未知地址":"招标人信息地址",
                                      "未知联系人":"招标人信息联系人",
                                      "未知电话":"招标人信息电话",
                                      "未知传真":"招标人信息传真",
                                      "未知邮箱":"招标人信息邮箱"
                                      },
                            "工程基本信息": {"估算价格": "工程基本信息估算价格"}}
replaceinfo_dict_zhongbiao={}
#content more than 100 not notice
more_than_len_100_true=[{"工程基本信息": "工程规模"}, {"工程招标信息": "招标内容"},{"工程招标信息":"招标范围"},{"工程基本信息":"项目简介"},{"工程基本信息":"项目规模"},{"工程招标信息":"标段范围"}
                        , {"工程招标信息": "标段投标人资质类别要求"}]
# 未知项目负责人资质等级


if __name__ == '__main__':
    pass
