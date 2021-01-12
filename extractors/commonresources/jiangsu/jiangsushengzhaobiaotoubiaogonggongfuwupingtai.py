# -*- coding: utf-8 -*- 
# @Time : 2020/11/23 11:22 
# @Author : limpo 
# @File : JiangSuShengZhaoBiaoTouBiaoGongGongFuWuPingTai.py 
# @desc: [ "更正公告公示", "中标结果公示", "中标候选人公示", "招标公告", "资格预审公告" ]
# 654，22464，23640，33085，76。总数：80604。 中标结果公示，招标公告

from scrapy.selector import Selector
from spidertools.utils.xpath_utils import get_alltext, get_all_tables
from spidertools.utils.text_utils import replace_punctuation
from spidertools.utils.snippets import combine_two_dict
import json

# from elog import extractlog
from extractors.base_extractor import BaseExtractor, _checkjson
from info_fsm import InfoMachine
from pprint import pprint
import re
import json

from table_info_extract.extract_utils import table_info_extract_styletwo, table_info_extract_stylethree
from table_info_extract import dict_mapping_triedTree

from table_info_extract.common_table_utils import common_table_extrator
from utils.logger_utils import savelog

def _del_nonormal_text(text):
    sublist = ["自中标结果公示之日起的三个工作日内，若对中标结果没有异议的，招标人将签发中标通知书；如对中标结果持有异议，请于公示时间内向中汽研汽车工业工程（天津）有限公司书面投诉。","注：各投标人对本次结果如有异议，请自本公告发出之日起七个工作日内，向昆山市中建项目管理有限公司提出质疑，七个工作日以外的质疑请求不再受理。","""""<div class="text-indent">2.内容：</div>""","采购网（网址：","第一开标室（地址：", "第二开标室（地址：", "发布日期:", "发布日期：", "更正公告发布时间：","值在投标文件开启（解密）前由招标人（或招标代理机构）或其委托的公证机构随机抽取确定。"
               "法人 （电子签名）：","招标人或者其委托的招标代理机构 （电子公章）：","   ","""<span style="font-family: 宋体; font-size: 14px;"><span style="font-family: 宋体;">二港池二期道堆场项目（陆域面积</span>20.73万，含两个丙类仓库）</span>"""
               "（<span>65</span>分）","<SPAN>(17</SPAN>分<SPAN>)","投标报价：&nbsp; 50&nbsp;&nbsp; 分"
               """<span style="font-family: 宋体; font-size: 19px;"><span style="font-family: 宋体;">投标保证金的金额：</span></span>""","，电话：",
               "网址：","投标保证金的金额：","交易中心（地址：","苏州市公共资源交易中心四楼开标室（地址：","招标人予以拒收。建议：","""<td width="111" style="border: 1px solid black; border-image: none;"><p><span style="font-size: 16px;">投标报价</span></p><p><span style="font-size: 16px;">（20分）</span></p></td>"""]

    sublist1=["采购结果公告期限为","成交人","商务部分赋分表","投标人必须在投标文件解密","评分标准","本项目投标","本次招标共计两个标段","本项目采用远程","设置一级监理机构"
              ,"特别提醒","为保障各潜在投标人投标权益","本项目只接受","本项目拟分阶段","投标人自2017年1月1日（含）以来","其它","3项目经理无在建工程",
              "本次招标采用资格后审","评标办法","评分细则","投标人不存在苏交监察","招标文件未明列的无效标条款","本次招标项目不安排专门的现场踏勘及考察","其他","因业主原因","备注","招标范围及标段划分"]
    sublist2=["，地址：","（地址："]
    for _sub in sublist:
        text = text.replace(_sub, "")

    for _sub1 in sublist1:
        text = text.replace(_sub1, _sub1+"：")

    for _sub2 in sublist2:
        text = text.replace(_sub2, "(")
    return text
def _del_nonormal_field_weizhi(result):
    """
    去除非正常Email：/Email：
    :param result:
    :return:
    """
    keys_values = [{"未知名称": "规格"},
                   {"未知邮箱":"/:E-mail"},
                   {'未知名称': '国信CA'},
                   {"邮编": "E-mail:sqzt001@163.com"},
                   {"邮箱":"邮编:223800"},
                   {"未知邮箱":"邮编:223800"},
                   {"未知名称": "司"},
                   {"未知官网地址": "https://zbcg.jchc.cn/index.html)列入失信名录的单位。"}]
    dict_weizhi=result.get("未知")
    if dict_weizhi:
        del_fields = []
        for key,value in dict_weizhi.items():
            key_value={key:value}
            if key_value in keys_values:
                del_fields.append(key)
        if del_fields:
            for del_field in del_fields:
                del result["未知"][del_field]
        return result
    else:
        return result
class JiangSuShengZhaoBiaoTouBiaoGongGongFuWuPingTai(BaseExtractor):
    def filter_tags(self, htmlstr):
        # 先过滤CDATA
        re_cdata = re.compile('//<!\[CDATA\[[^>]*//\]\]>', re.I)  # 匹配CDATA
        re_script = re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>', re.I)  # Script
        re_style = re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>', re.I)  # style
        re_br = re.compile('<br\s*?/?>')  # 处理换行
        re_h = re.compile('</?\w+[^>]*>')  # HTML标签
        re_comment = re.compile('<!--[^>]*-->')  # HTML注释
        s = re_cdata.sub('', htmlstr)  # 去掉CDATA
        s = re_script.sub('', s)  # 去掉SCRIPT
        s = re_style.sub('', s)  # 去掉style
        s = re_br.sub('\n', s)  # 将br转换为换行
        s = re_h.sub('', s)  # 去掉HTML 标签
        s = re_comment.sub('', s)  # 去掉HTML注释
        # 去掉多余的空行
        blank_line = re.compile('\n+')
        s = blank_line.sub('\n', s)
        s = s.replace(" ", "")
        s = re.sub(r'\\n|\xa0|\\t|\\r|\t\t', '', s)
        s = self.replaceCharEntity(s)  # 替换实体
        s = s.lower()
        return s

    ##替换常用HTML字符实体.
    # 使用正常的字符替换HTML中特殊的字符实体.
    # 你可以添加新的实体字符到CHAR_ENTITIES中,处理更多HTML字符实体.
    # @param htmlstr HTML字符串.
    def replaceCharEntity(self, htmlstr):
        CHAR_ENTITIES = {'nbsp': ' ', '160': ' ',
                         'lt': '<', '60': '<',
                         'gt': '>', '62': '>',
                         'amp': '&', '38': '&',
                         'quot': '"', '34': '"', }

        re_charEntity = re.compile(r'&#?(?P<name>\w+);')
        sz = re_charEntity.search(htmlstr)
        while sz:
            entity = sz.group()  # entity全称，如&gt;
            key = sz.group('name')  # 去除&;后entity,如&gt;为gt
            try:
                htmlstr = re_charEntity.sub(CHAR_ENTITIES[key], htmlstr, 1)
                sz = re_charEntity.search(htmlstr)
            except KeyError:
                # 以空串代替
                htmlstr = re_charEntity.sub('', htmlstr, 1)
                sz = re_charEntity.search(htmlstr)
        return htmlstr

    def parse_bid_evaluation_results_announcement(self):
        '''
        评标结果公告提取
        :return:
        '''
        body_text = get_alltext(self.sel.xpath('//body'))
        machine = InfoMachine(self.base_pattern)
        clean_text = replace_punctuation(body_text.strip())

        output = machine.run_list([clean_text])
        # output_dict = combine_two_dict(output, self.info_dict)

        tables = get_all_tables(self.sel)
        for table in tables:
            result = common_table_extrator(table)
            if result:
                output = combine_two_dict(output, result)

        zhaobiao_own = self.sel.xpath("//*[@id='lblJsDW']/text()")
        if zhaobiao_own:
            ower = zhaobiao_own.extract()[0]
            if ower:
                if '工程招标信息' not in output:
                    output['工程招标信息'] = {}

                if '招标人信息名称' not in output['工程招标信息']:
                    output['工程招标信息']['招标人信息名称'] = []
                if ower not in output['工程招标信息']['招标人信息名称']:
                    output['工程招标信息']['招标人信息名称'].append(ower)

        xiangmu_name = self.sel.xpath("//*[@id='lblBDName']/text()")
        if xiangmu_name:
            name = xiangmu_name.extract()[0]
            if '工程招标信息' not in output:
                output['工程招标信息'] = {}

            if '标段名称' not in output['工程招标信息']:
                output['工程招标信息']['标段名称'] = name
        return output

    def parse_not_shortlisted_announcement(self):
        '''
                评标未入围公告信息提取
                :return:
                '''
        output_dict = {}
        tables = get_all_tables(self.sel)
        for table in tables:
            result = common_table_extrator(table)
            output_dict = combine_two_dict(output_dict, result)

        return output_dict

    def commom_announcement_parse(self):
        '''
        通用网页公告解析
        :return:
        '''

        # 获取招标公告正文
        content_root_nodes = self.sel.xpath('//body')
        texts = []

        # 遍历所有子节点，获取相应的文本
        for node in content_root_nodes:
            node_text = get_alltext(node)
            texts.append(node_text)
        clean_texts = []
        # 清理文本中的一些空几个，不可见字符，以及加载关键字中间的空格
        for text in texts:
            text = replace_punctuation(text.strip())
            clean_texts.append(text)
        clean_texts = [
            '1、项目名称:南京长江大桥公路桥维修改造工程2、招标编号:njjt20180612740备案号:苏交建备njjt[2018]0238号3、项目信息:4、标段信息:5、建设地点:南京市6、专业:其它招标种类:监理招标内容:(1)项目概况南京长江大桥是我国第一座自行设计、施工的铁路双线,公路双向四车道的公铁两用桥,公路桥全长4588m(铁路桥全长6772m)。其中:公路正桥(公铁两用)全长1576m(共10跨),北岸(浦口)公路引桥全长1247m(涉铁段引桥7孔,公路引桥31孔),南岸(鼓楼)公路引桥全长1765m(涉铁段引桥7孔,公路引桥46孔),南岸分岔落地公路桥(回龙桥)12孔。南京长江大桥是我国第一座自行设计、施工的跨越长江天堑的公铁两用特大桥,自1968年全面建成通车至今(2015年)已运营47年。在47年多的运营过程中,由于公路桥实际通行荷载大原设计标准等级,通行交流量远超设计供需不平衡造成大桥严重壅塞的同时,常引起桥梁构件的损坏。自2002年以来虽经过多次大规模的维修,但由于交通压力过大、超限车辆夜间强行过桥等原因,公路桥病害始终无法得到及时和彻底地处治,结构性及耐久性病害日益突出。大桥目前存在的病害,已经对结构安全、铁路运营及公路交通安全产生严重影响,因此对大桥进行全封闭的维修改造。(2)招标范围本次招标项目为南京长江大桥公路桥维修改造工程机电施工监理项目ⅲ标段,招标范围如下:南京长江大桥公路桥维修改造工程亮化照明系统的施工监理,以及相关临时工程的施工监理工作。本项目设置一级监理机构,为总监理工程师办公室。施工阶段监理服务期:计划3个月。监理服务缺陷责任期:24个月。计划开工时间:2018-07-10计划竣工时间:2018-10-10']
        # 创建状态机
        machine = InfoMachine(self.base_pattern)
        # 执行状态机，解析整个文本
        output_dict = machine.run_list(clean_texts)

        # 获取所有的table表格
        tables = get_all_tables(self.sel)
        for table in tables:
            result = common_table_extrator(table)
            output_dict = combine_two_dict(output_dict, result)

        return output_dict

    def fittler_project(self, txt):
        for key_word in ['零配件', '日常防水维修工程']:
            if key_word in txt:
                return False
        else:
            return True

    def judge_bid_field(self,data):
        if "data" in data.keys():
            if "data" in data['data'].keys():
                if data["data"]["data"]:
                    fields=['bulletincontent','projectName','bidsectioncodes']
                    allfields=[i for i in data["data"]["data"][0].keys()]
                    if fields==[i for i in fields if i in allfields]:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:return False
    def win_judge_field(self,data):
        if "data" in data.keys():
            if "data" in data['data'].keys():
                if data["data"]["data"]:
                    fields=['bulletincontent']
                    allfields=[i for i in data["data"]["data"][0].keys()]
                    if fields==[i for i in fields if i in allfields]:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:return False

    def parse_win_bidding_announcement(self):
        '''
        中标公告信息提取
        :return:
        '''
        # 获取招标公告正文
        api_html_content_=""
        json_output_dict={}
        try:
            data = json.loads(self.html)
            if self.win_judge_field(data):
                api_html_content_ = data['data']['data'][0]['bulletincontent']
                # 项目名称
                projectName = data['data']['data'][0]['tenderprojectname']
                # 标段编号
                bidsectioncodes = data['data']['data'][0]['bidsectioncodes']
                # 标段名称
                bulletinname = data['data']['data'][0]['bulletinname']
                bulletinname = bulletinname.replace("结果公告", "")
                if not projectName:
                    projectName = ""
                if not bidsectioncodes:
                    bidsectioncodes=""
                if not bulletinname:
                    bulletinname=""

            json_output_dict = {"工程基本信息": {"项目名称": projectName},
                                "工程招标信息": {"标段编号": bidsectioncodes,
                                           "标段名称": bulletinname}}
        except Exception as e:
            api_html_content_=self.html.replace("tenderprojectname","项目名称")\
                .replace("bidsectioncodes","标段编号")\
                .replace("bulletinname","标段名称")\
                .replace("projectName","项目名称")\
                .replace(r"\n","")\
                .replace("\\","")\
                .replace("'","")\
                .replace('"','')\
                .replace("null","")
        api_html_content_ = _del_nonormal_text(api_html_content_)
        texts = [self.filter_tags(api_html_content_)]
        # 创建状态机
        machine = InfoMachine(self.base_pattern)
        clean_texts = []
        # 清理文本中的一些空几个，不可见字符，以及加载关键字中间的空格
        for text in texts:
            text = replace_punctuation(text.strip().replace(" ",""))
            clean_texts.append(text)
        # 执行状态机，解析整个文本
        output_dict = machine.run_list(clean_texts)
        output_dict = combine_two_dict(json_output_dict, output_dict)
        re_sel = Selector(text=api_html_content_)
        tables = get_all_tables(re_sel)
        for table in tables:
            result = common_table_extrator(table)
            output_dict = combine_two_dict(output_dict, result)
        html_info_dict = dict_mapping_triedTree(self.info_dict)
        output_dict = combine_two_dict(output_dict, html_info_dict)
        return output_dict

    def parse_bid_announcemen(self):
        '''
        招标信息提取f
        :param root:
        :return:p
        '''
        # 获取招标公告正文
        api_html_content_=""
        json_output_dict={}
        try:
            data = json.loads(self.html)
            if self.win_judge_field(data):
                api_html_content_ = data['data']['data'][0]['bulletincontent']
                # 项目名称
                projectName = data['data']['data'][0]['projectName']
                # 标段编号
                bidsectioncodes = data['data']['data'][0]['bidsectioncodes']
                # 标段名称
                bulletinname = data['data']['data'][0]['bulletinname']
                bulletinname = bulletinname.replace("招标公告", "")
                if not projectName:
                    projectName = ""
                if not bidsectioncodes:
                    bidsectioncodes=""
                if not bulletinname:
                    bulletinname=""

            json_output_dict = {"工程基本信息": {"项目名称": projectName},
                                "工程招标信息": {"标段编号": bidsectioncodes,
                                           "标段名称": bulletinname}}
        except Exception as e:
            api_html_content_=self.html.replace("bidsectioncodes","标段编号")\
                .replace("bulletinname","标段名称")\
                .replace("projectName","项目名称")\
                .replace(r"\n","")\
                .replace("\\","")\
                .replace("'","")\
                .replace('"','')\
                .replace("null","")
        api_html_content_=_del_nonormal_text(api_html_content_)
        texts = [self.filter_tags(api_html_content_)]
        # 创建状态机
        machine = InfoMachine(self.base_pattern)
        clean_texts = []
        # 清理文本中的一些空几个，不可见字符，以及加载关键字中间的空格
        for text in texts:
            text = replace_punctuation(text.strip().replace(" ",""))
            clean_texts.append(text)
        # 执行状态机，解析整个文本
        output_dict = machine.run_list(clean_texts)
        output_dict = combine_two_dict(json_output_dict, output_dict)
        re_sel = Selector(text=api_html_content_)
        tables = get_all_tables(re_sel)
        for table in tables:
            result = common_table_extrator(table)
            output_dict = combine_two_dict(output_dict, result)
        html_info_dict = dict_mapping_triedTree(self.info_dict)
        output_dict = combine_two_dict(output_dict, html_info_dict)
        output_dict = _del_nonormal_field_weizhi(output_dict)
        return output_dict

    def start_parse(self):
        result = {}
        if '招标公告' in self.info_dict['公告类型']:
            result = self.parse_bid_announcemen()
        elif '中标公告' in self.info_dict['公告类型']:
            result = self.parse_win_bidding_announcement()
        elif '未入围公示' in self.info_dict['公告类型']:
            pass
            # result = self.parse_not_shortlisted_announcement()
        elif '评标结果公示' in self.info_dict['公告类型']:
            pass
            # result = self.parse_bid_evaluation_results_announcement()

        self.info_dict['公告类型'] = self.info_dict['公告类型'].replace("\r\n", "").replace(" ", "")
        html_info_dict = dict_mapping_triedTree(self.info_dict)
        result = combine_two_dict(result, html_info_dict)
        return result

    def get_line_like_nodes(self, roots):
        node_list = []

        sub_nodes = roots.xpath('./*')
        for sub_node in sub_nodes:
            if sub_node.attrib and ('id' in sub_node.attrib):
                id = sub_node.attrib['id']
            else:
                id = ""
            if id == 'zygg_kkk':
                node_list.extend(self.get_line_like_nodes(sub_node))
            else:
                if sub_node.root.tag != 'table':
                    node_list.append(sub_node)
                else:
                    tr_nodes = sub_node.xpath(".//tr")
                    for tr in tr_nodes:
                        node_list.append(tr)
        return node_list


if __name__ == '__main__':
    origin_urls = []
    with open(r"C:\Users\linpo\Desktop\sample.txt", 'r',encoding='utf-8') as f:
        for content1 in list(f):
            content = content1.split("##")[-1]
            info_dict = {}
            info_dict['html'] = content
            info_dict['公告类型'] = "招标公告"#中标公告
            info_dict['_id'] = 'id123'
            obj = JiangSuShengZhaoBiaoTouBiaoGongGongFuWuPingTai(info_dict)
            result = obj.parse_bid_announcemen()
            result["工程公告信息"]={"公告类型":"招标公告"}
            LogStateString_dict,result= _checkjson(result)
            print("LogStateString_dict:",LogStateString_dict)
            pprint(result)
            print("====================================================================")
            for  logstatestring, list  in LogStateString_dict.items():
                savelog(logstatestring, "#".join(list), msg_dict=result)
