# -*- coding: utf-8 -*-
from scrapy.selector import Selector
from spidertools.utils.xpath_utils import get_alltext, get_all_tables
from spidertools.utils.text_utils import replace_punctuation, clean_html_whitesplace
from spidertools.utils.snippets import combine_two_dict
from configs.commom import notice_style_dic, notice_style_zhongbiao, notice_style_zhaobiao, replaceinfo_dict_zhaobiao, \
    replaceinfo_dict_zhongbiao, more_than_len_100_true, list_key
from utils.logger_utils import savelog, LogStateString
from info_fsm import InfoMachine
from table_info_extract.common_table_utils import common_table_extrator
from table_info_extract import dict_mapping_triedTree
import copy
import os
from project_setting import KEYWORDS_EXTEND_DATA_PATH, NO_NEED_CHECK_URL_DIR


def _checklength(doc):
    realfirstlist = []
    realsecondlist = []
    for k, v in doc.items():
        if isinstance(v, dict):
            realfirstlist.append(k)
            realsecondlist.append([i for i in doc[k].keys()])

    realfirst_content_list = []
    realsecond_content_list = []
    for k, v in doc.items():
        if isinstance(v, list):
            realfirst_content_list.append(k)
            tmp_keys = []
            if v:
                for i in v:
                    tmp_keys.append(list(i.keys())[0])
            tmp_keys = list(set(tmp_keys))
            realsecond_content_list.append(tmp_keys)
    # 内容为list
    # '工程投标信息': [{'中标信息名称': '苏州市庙港建筑有限公司'},{'中标信息名称': '苏州市庙港建筑有限公司\t\t\xa0\t\t\xa0\t\t\t\t资质证书号码:\t\tD232048511\t\t资质等级:\t\t房屋建筑工程二级;'}],

    content_100_field_str = {}
    for k, v in zip(realfirst_content_list, realsecond_content_list):
        if len(v) != 0:
            for content_dict in doc[k]:
                if isinstance(content_dict, dict):
                    for key, value in content_dict.items():
                        if len(value) > 100:
                            content_100_field_str[key] = value
        else:
            del doc[k]
    for k, v in zip(realfirstlist, realsecondlist):
        if len(v) != 0:
            ##一级目录为空
            for i in v:
                content = doc[k][i]
                # data=[]
                if type(content) == list:
                    if len(content) == 0:
                        # content_list_0.append({k: i})
                        del doc[k][i]
                    else:
                        # data=["","","",""]
                        for j in content:
                            if len(j) == 0:
                                # content_list_content_0.append({k: i})
                                del doc[k][i]
                            elif len(j) > 100 and {k: i} not in more_than_len_100_true:
                                content_100_field_str[i] = j
                            else:
                                pass
                elif type(content) == str:
                    if len(content) == 0:
                        # content_0.append({k: i})
                        del doc[k][i]
                    elif len(content) > 100 and {k: i} not in more_than_len_100_true:
                        content_100_field_str[i] = content
                    else:
                        pass
        else:
            del doc[k]

    LogStateString_dict = {}
    ###長度内容為100
    if content_100_field_str:
        LogStateString_dict[LogStateString.Waring_ContentLenMoreThan100] = content_100_field_str
    return LogStateString_dict


def _checktype(doc):
    # 检查在list_key中（是list),但不是
    first_second_keys = []
    for key, values in doc.items():
        if type(values) == dict:
            for val in values.keys():
                first_second_keys.append({key: val})
        elif type(values) == list:
            for value in values:
                if type(value) == dict:
                    for val in value.keys():
                        first_second_keys.append({key: val})
    fatalerror_typenotdict = {}
    for first_second_key in first_second_keys:
        first_key = list(first_second_key.keys())[0]
        second_key = list(first_second_key.values())[0]
        if second_key in list_key:  # 规定的list,不是list，报error，
            if isinstance(doc[first_key], dict):
                content = doc[first_key][second_key]
                if not isinstance(content, list):
                    fatalerror_typenotdict[second_key] = content
            elif isinstance(doc[first_key], list):
                for values in doc[first_key]:
                    for val, list_ in values.items():
                        if not isinstance(list_, list) and val in list_key:
                            fatalerror_typenotdict[val] = list_

    return fatalerror_typenotdict


def _checkjson(doc):
    # 页面是否正常，返回空
    if doc.get("the_page"):
        return {}, None
    notice_style = doc["工程公告信息"]['公告类型']  # 公告类型
    secondkeys = {}

    if notice_style in notice_style_zhongbiao:
        # 中标缺失字段
        secondkeys = {"工程公告信息": ['工程公告信息发布时间', '公告标题'], "工程基本信息": ['项目名称'], "工程投标信息": ['中标信息名称']}
    elif notice_style in notice_style_zhaobiao:
        # 招标缺失字段
        secondkeys = {"工程基本信息": ['项目名称'], "工程招标信息": ['标段名称']}
    secondkeyslist = []
    firstkeyslist = []
    for k, v in secondkeys.items():
        secondkeyslist.extend(v)  # as ['工程公告信息发布时间', '公告标题'],
        firstkeyslist.append(k)  # as 工程公告信息
    alllist = []
    alllist.extend(secondkeyslist)
    alllist.extend(firstkeyslist)

    allreallist = []
    realfirstlist = []
    realsecondkeyslist = []
    for k, v in doc.items():
        realfirstlist.append(k)  # 实际doc
        if type(v) == dict:
            realsecondkeyslist.extend([i for i in v.keys()])
        elif type(v) == list:
            if v:
                for i in v:
                    if type(i) == dict:
                        realsecondkeyslist.extend([j for j in i.keys()])
    allreallist.extend(realfirstlist)
    allreallist.extend(realsecondkeyslist)

    # blackpink =Ture，不缺字段，False 缺字段
    # 如果有flag,没有‘项目名称’,true
    if "flag" in realsecondkeyslist:  # 特殊情况，结果中无项目名称
        alllist.remove("项目名称")
        diff = [i for i in alllist if i in allreallist]
        blackpink = (diff == alllist)
    else:
        diff = [i for i in alllist if i in allreallist]  # diff 交集
        blackpink = (diff == alllist)

    if "未知" in allreallist:
        # 有未知 key，不缺字段
        doc = _translatedict(doc)
    else:
        doc = doc

    # 检查字段内容 0-100
    LogStateString_dict = _checklength(doc)

    # 检测联系人内容格式list
    fatalerror_typenotlist = _checktype(doc)
    if fatalerror_typenotlist:
        LogStateString_dict[LogStateString.FatalError_TypeNotList] = fatalerror_typenotlist

    if blackpink == True:  # 有未知错误
        if "未知" in doc.keys():
            # WeiZhiKeyWords=[i for i in doc["未知"].keys()]
            WeiZhiKeyWords = doc["未知"]
            LogStateString_dict[LogStateString.Waring_WeiZhiKeyWords] = WeiZhiKeyWords
            # return LogStateString.Waring_WeiZhiKeyWords,WeiZhiKeyWords
        else:
            LogStateString_dict["success"] = []
            # return "success",[]
    else:# 有未知错误
        # 缺关键词
        lockkeywords = [i for i in alllist if i not in allreallist]
        LogStateString_dict[LogStateString.FatalError_LockKeyWords] = lockkeywords
        if "未知" in doc.keys():
            # WeiZhiKeyWords=[i for i in doc["未知"].keys()]
            WeiZhiKeyWords = doc["未知"]
            LogStateString_dict[LogStateString.Waring_WeiZhiKeyWords] = WeiZhiKeyWords
    return LogStateString_dict, doc


def _check_exist(field, fields):
    if field in fields:
        return True
    else:
        return False


def changedict(result, replaceinfo_dict):
    weizhidict = result['未知']
    change_first_field = replaceinfo_dict.keys()
    for first_field in change_first_field:
        for changek_second, changev_second in replaceinfo_dict[first_field].items():
            if changek_second in weizhidict.keys():
                if first_field not in result.keys():
                    result[first_field] = {}
                    result[first_field][changev_second] = weizhidict[changek_second]
                    del weizhidict[changek_second]
                else:
                    if changev_second not in result[first_field].keys():
                        result[first_field][changev_second] = {}
                        result[first_field][changev_second] = weizhidict[changek_second]
                        del weizhidict[changek_second]
    if not weizhidict:
        del result['未知']
    return result


def _translatedict(result):
    if result["工程公告信息"]['公告类型'] in notice_style_zhaobiao:
        result = changedict(result, replaceinfo_dict_zhaobiao)
        return result
    elif result["工程公告信息"]['公告类型'] in notice_style_zhongbiao:
        result = changedict(result, replaceinfo_dict_zhongbiao)
        return result
    else:
        return result


class BaseExtractor(object):
    def __init__(self, info_dict):
        '''
        info_dict,从mongo数据库里面拿到的dict对象
        '''
        self.info_dict = copy.deepcopy(info_dict)
        self.html = info_dict['html']
        self.sel = Selector(text=self.html)
        self.base_pattern = '%s:\s*(.*)'
        del self.info_dict['html']
        del self.info_dict['_id']

        self.no_needcheck_list = self.get_no_needcheck_urls(self.info_dict['province'], self.info_dict["source_type"])
        self.extend_keywords = self.get_extend_keywords(self.info_dict['province'], self.info_dict["source_type"])

    def get_no_needcheck_urls(self, province, source_type):
        '''
        根据province和source_type,获取到不需要提取的urls列表
        '''
        result_set = set()
        file_path = os.path.join(NO_NEED_CHECK_URL_DIR, province, source_type)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as fread:
                for line in fread:
                    result_set.add(line.strip())
        return list(result_set)

    def get_extend_keywords(self, province, source_type):
        '''
            根据province和source_type,获取到额外网站单独处理的词条
            mode  type    keyword
            +   common_电话    咨询电话
            -   ingore  咨询电话
        '''
        add_keys = []
        file_path = os.path.join(KEYWORDS_EXTEND_DATA_PATH, province, source_type)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as fread:
                for line in fread:
                    # mode,type,keyword = line.strip().split("\t")
                    add_keys.append(line.strip().split(" "))
        return add_keys

    def common_text_parse(self, xpath='//body'):
        '''

        '''
        # 获取招标公告正文
        content_root_nodes = self.sel.xpath(xpath)
        texts = []

        # 遍历所有子节点，获取相应的文本
        for node in content_root_nodes:
            node_text = get_alltext(node)
            texts.append(node_text)

        clean_texts = []
        # 清理文本中的一些空几个，不可见字符
        for text in texts:
            text = replace_punctuation(text.strip())
            clean_texts.append(text)

        # 创建状态机
        machine = InfoMachine(self.base_pattern, extend_keywords=self.extend_keywords)
        # 执行状态机，解析整个文本
        output_dict = machine.run_list(clean_texts)

        return output_dict

    def common_table_parse(self):
        # 获取所有的table表格
        output_dict = {}
        tables = get_all_tables(self.sel)
        for table in tables:
            result = common_table_extrator(table)
            output_dict = combine_two_dict(output_dict, result)
        html_info_dict = dict_mapping_triedTree(self.info_dict)
        output_dict = combine_two_dict(output_dict, html_info_dict)
        return output_dict

    def commom_announcement_parse(self):
        '''
        通用网页公告解析
        :return:
        '''

        text_parsed_dicts = self.common_text_parse()
        table_parsed_dicts = self.common_table_parse()
        output = {}
        if text_parsed_dicts:
            output = combine_two_dict(output, text_parsed_dicts)
        if table_parsed_dicts:
            output = combine_two_dict(output, table_parsed_dicts)

        return output

    def start_parse(self):
        '''
        如果通用提起不能完全提取出来，则自己根据自己的需求，在写几个分支
        '''

        result = self.commom_announcement_parse()
        return result

    def combine_origin_dict(self, output):
        '''
        将解析以后的dict和最原始的info_dict进行合并
        '''
        html_info_dict = dict_mapping_triedTree(self.info_dict)
        result = combine_two_dict(output, html_info_dict)
        return result

    def output_extractor_dict(self):
        '''
        输出最终的提取结果
        '''

        clean_announcement = clean_html_whitesplace(self.info_dict['公告类型'])
        if clean_announcement not in notice_style_dic:
            return None
        self.info_dict['公告类型'] = notice_style_dic.get(clean_html_whitesplace(clean_announcement))
        extractor_output = self.start_parse()
        result = self.combine_origin_dict(extractor_output)
        # "未知":{"联系人":"xxx","传qwe真":"xxx","电话":"xxx"} 替换
        # 字段长度超过100 .和0，有些字典规定超过100
        LogStateString_dict, result = _checkjson(result)
        if LogStateString_dict:
            data = {}
            data["original_data"] = self.info_dict
            data["extract_data"] = result
            for logstatestring, _dict in LogStateString_dict.items():
                list_ = []
                if isinstance(_dict, dict):
                    for k, v in _dict.items():
                        list_.append(str(k) + ":" + str(v))
                elif isinstance(_dict, list):
                    list_ = _dict
                savelog(logstatestring, "#".join(list_), msg_dict=data)
                if logstatestring.startswith("FatalError"):
                    result = None

        return result


if __name__ == '__main__':
    # import requests
    #
    # zhaobiao_url = "http://www.jszb.com.cn/JSZB/yw_info/ZhaoBiaoGG/ViewReportDetail.aspx?RowID=745913&siteid=1&categoryNum=6"
    # zhongbiao_url = "http://www.jszb.com.cn/JSZB/yw_info/ZhongBiaoGS/ViewGSDetail.aspx?RowID=1297866&siteid=1&categoryNum=7"
    # not_in_url = "http://www.jszb.com.cn/JSZB/yw_info/ZiGeYS/ViewYSDetail.aspx?RowID=158068&siteid=1&categoryNum=8"
    # bid_evaulate_url = "http://www.jszb.com.cn/JSZB/yw_info/HouXuanRenGS/ViewHXRDetail.aspx?GongGaoGuid=ec62fb01-6c99-4863-aecc-6eb081380a30"
    #
    # req = requests.get(bid_evaulate_url)
    # info_dict = {}
    # info_dict['html'] = req.text
    # info_dict['公告类型'] = "招标公告"
    # obj = BaseExtractor(info_dict)
    # result = obj.commom_announcement_parse()
    # pprint(result)

    doc = {
        "_id": "5fb783d9f3e6911038fa18f7",
        "工程基本信息": {
            "项目编号": "",
            "项目名称": "",
            "工程规模": "滞洪区滞洪范围调整。将滞洪滞洪范围为徐洪河以东地区,滞洪区面积由调整前的357.8km2缩减为230km2；(2)蓄滞洪区工程建设。滞洪堤防复堤2.782km、堤防防渗处理4.95km。拆建、加固、新建穿围堤建筑物(包括分蓄退洪建筑物)共30座；(3)蓄滞洪区安全建设。新建、改建、扩建撤退道路条总长73.621km,拆建、新建、加固与撤退道路配套涵洞175座,拆建、新建、改造与撤退道路配套桥梁19座；(4)完善滞洪区预警预报系统；(5)蓄滞洪区管理体系建设。2017年3月江苏省发改委以苏发改农经发〔2017〕288号文批复《黄墩湖滞洪区调整与建设工程可行性研究报告》；2017年10月江苏省发改委以苏发改农经发〔2017〕1257号文批复《黄墩湖滞洪区调整与建设工程初步设计报告》。根据黄墩湖滞洪区调整与建设工程的实施计划进度安排,2017年度拟开工建设新邳洪河闸、黄墩湖滞洪闸加固工程。本标段的主要建设内容包括:黄墩湖滞洪闸改造工程的预埋件制作、闸门止水橡皮及压板等；新邳洪河闸加固工程钢闸门及预埋件制作、固定卷扬式启闭机及预埋件和检修门启闭机及预埋件采购等。 以上设备内容主要包括:闸门及其门槽埋件、检修门槽埋件的制作、防腐、检验、验收、装货、运输、配合安装和调试运行等。其中闸门包括其成套组成的各种零部件(含行走支承、止水、及埋件等)的采购、制作；闸门启闭所需的卷扬式启闭机(包含电机、减速箱、开式齿轮、制动器、机架、钢丝绳、开度荷载传感器、限速装置、上下限位装置、绳套或吊头、销轴、轴端挡板、启闭机机架下封尘板等保证启闭机正常运行的全部构件)、安装启闭设备所需的预埋件的设计、材料及元器件的采购、厂内制造、防腐、出厂前检验、包装、发运、现场检验、交货及配合安装调试等。"},
        "工程招标信息": {
            "招标人信息名称": [
                "江苏省监狱管理局",
                "江苏省政府采购中心"
            ],
            "招标人信息地址": [
                "南京江东北路188＃",
                "南京市汉中门大街145号江苏省公共资源交易中心二期3楼"
            ],
            "招标人信息联系人":
                "李士康",
            "招标人信息电话": [
                "025-862650282.江苏省政府采购中心信息",
                "025-83668516        江苏省政府采购中心          2020年11月20日附件:江苏省监狱管理局江苏省监狱管理局服务器采购公开招标采购文件JSZC-G2020-471.doc",
                "025-83633702  联系邮箱:jszfcgbx@163.com      "
            ]
        },
        "工程投标信息": {
            "中标信息名称": "2U机架式服务器品牌:中兴通讯规格型号:ZXCLOUD R5300 G4数量:52单价:22520五、评审专家名单:顾永忠  汤俊彦 吴义泽 薛翔 马春宝六、代理服务收费标准及金额:本项目不收取代理服务费。七、公告期限自本公告发布之日起1个工作日。八、其他补充事宜无。九、本次中标公告联系方式1.",
            "中标信息地址": "南京市建邺区庐山路230号",
            "中标金额": "壹佰壹拾柒万壹仟零肆拾元整 人民币四、"
        },
        "工程公告信息": {
            "公告标题": "江苏省监狱管理局江苏省监狱管理局服务器采购公开招标中标公告",
            "工程公告信息发布时间": "2020-11-20",
            "公告类型": "招标公告"
        },
        "原始地址": "http://api.jszbtb.com/DataSyncApi/WinBidBulletin/id/103081",
        "公告类型": "招标公告",
        "未知": {
            "联系人": "联系人1",
            "电话": "电话1",
            "传真": "传真1",
            "估算价格": "估算价格1"
        },
        "工程公告信息发布时间": "2020-04-20",
        "search_key": "http://api.jszbtb.com/DataSyncApi/WinBidBulletin/id/103081$$中标结果公示$$2020-04-20",
        "is_parsed": 0,
        "create_time": "2020-12-08 16:08:47",
        "update_time": "2020-12-08 16:08:47"
    }
    # print(_checklength(doc))
    _checkjson(doc)

#    doc={'工程基本信息': {"项目名称":"项目名称",
#                       '工程地址': '吴江区太湖新城吴模路1855号',
#                       '工程所属地区': '320584',
#                       '工程类别': '建设工程 '},
#         '工程招标信息': {'招标人信息电话': 555,"招标人信息联系人":123},
#            '工程投标信息': [
#                {'中标信息名称': '苏州qeeeeeeeeeerwqrqqwwwwwwwwwwqeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeewwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww市庙港建筑有限公司'},
#                       {'中标信息名称': '苏州市庙港建qweeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee筑有限公司\t\t\xa0\t\t\xa0\t\t\t\t资质证书号码:\t\tD232048511\t\t资质等级:\t\t房屋建筑工程二级;'}],
#            '未知': {"未知联系人":"444","未知电话":["123456"]},
#            '工程公告信息': {'公告标题': '吴江区实验初级中学改扩建工程苏州市吴江区实验初级中学改扩建工程-土建总包中标结果公告',
#                       '工程公告信息发布时间': '2020-11-23',
#                       '公告类型': '招标公告'}}
#
# #    doc={'工程公告信息': {'公告标题': '春晖路人行道改造工程', '公告类型': '招标公告', '工程公告信息发布时间': '2020-06-28'},
# # '工程基本信息': {'工程开工时间': '2020-07-30',
# #            '工程竣工时间': '2020-10-27',
# #            '工程类别': '建设工程 ',
# #            '工程规模': '本工程为春晖路(长江路-青阳路)段南北两侧人行道改造,道路长度1473m,现场拌制彩色透水混凝土人行道改造铺装面积约17789平方米；雨水管HDPE双壁波纹管DN225约616米,成品缝隙式U型树脂混凝土排水沟约2226米。',
# #            '建筑面积': '0',
# #            '项目名称': '春晖路人行道改造工程'},
# # '工程招标信息': {'招标内容': '春晖路人行道改造工程(大型土石方、人行道铺装、雨水管道)',
# #            '标段估价': '1377',
# #            '标段名称': '春晖路人行道改造工程',
# #            '标段编号': 'G20200309'},
# # '未知': {'未知地址': '昆山市萧林路189号光大广场5楼',
# #        '未知电话': ['0512-57172999'],
# #        '未知联系人': ['张爱忠']}}
#    info_dict={
#    "_id" : "5fbb3628acf2fd88c90d391f",
#    "html":"123",
#    "公告标题" : "全过程工程咨询服务中标结果公告",
#    "公告发布时间" : "2018-10-19",
#    "区域" : "省级",
#    "origin_url" : "http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20181019/d30a5060-f9d5-4576-a39f-4ba71150e9a3.html",
#    "is_parsed" : 1,
#    "source_type" : "江苏公共资源交易网",
#    "province" : "江苏",
#    "city" : "省级",
#    "公告类型" : "中标结果公告",
#    "工程类型" : "建设工程 "
#        }
#    # LogStateString_dict, result = _checkjson(doc)
#    # if LogStateString_dict:
#    #     del info_dict["html"]
#    #     data = {}
#    #     data["original_data"] = info_dict
#    #     data["extract_data"] = result
#    #     for logstatestring, _dict in LogStateString_dict.items():
#    #         list_ = []
#    #         if isinstance(_dict, dict):
#    #             for k, v in _dict.items():
#    #                 list_.append(str(k) + ":" + str(v))
#    #         elif isinstance(_dict, list):
#    #             list_ = _dict
#    #         savelog(logstatestring, "#".join(list_), msg_dict=data)
#    #         if logstatestring.startswith("FatalError"):
#    #             result = None
#    # else:
#    #     pass
#
#    pprint(_translatedict(doc))
