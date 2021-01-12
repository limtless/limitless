# -*- coding:utf-8 -*-
from scrapy.selector import Selector
from spidertools.utils.xpath_utils import get_alltext,get_all_tables
from spidertools.utils.text_utils import replace_punctuation
from spidertools.utils.snippets import combine_two_dict
from info_fsm import InfoMachine
import sys
from pprint import pprint
import requests
from table_info_extract.extract_utils import table_info_extract_styletwo,table_info_extract_stylethree
from table_info_extract import dict_mapping_triedTree
from table_info_extract.common_table_utils import common_table_extrator
from extractors.base_extractor import BaseExtractor
import os
import json
import re
from lxml import etree


class JiangSuShengGongLuShuiLuJianSheShiChangXinYongXinXiFuWuXiTong(BaseExtractor):

    def start_parse(self):
        # if '跳转前网页' in self.html:  #如果是json格式的，用json解析（仅供本地测试使用）
        if self.html.startswith('{'):#传入的数据若以{为开头，则为json格式的网页
            result = self.new_json_parse(self.html)
            html_info_dict = dict_mapping_triedTree(self.info_dict)
            if result:   #如果网页解析返回值正常
                result = combine_two_dict(result, html_info_dict)
                return result
            else:
                print('网页出错，格式不同')
        else:
            if self.info_dict['公告类型'] == '中标公告':
                result = self.common_table_parse()
            else:
                result=self.new_commom_announcement_parse()#调用表格解析模块
                html_info_dict = dict_mapping_triedTree(self.info_dict)
                result = combine_two_dict(result, html_info_dict)
            return result

    def new_commom_announcement_parse(self):
        self.html = replace(self.html)
        self.sel = Selector(text=self.html)
        output_dict={}
        tables=[]
        #获取所有的table表格
        content_root_nodes = self.sel.xpath("//div[@class='tips noline']")
        for node in content_root_nodes:
            node_text = str(node.xpath('string(.)')[0])
            if '、预约' in node_text:
                continue
            elif '、招标投标文件' in node_text:
                continue
            elif '、监管单位' in node_text:
                continue
            else:
                table_nodes = node.xpath(".//table")
                tables.extend(table_nodes) #extend加一整个列表

        # tables = get_all_tables(self.sel)
        for table in tables:
            result = common_table_extrator(table)
            output_dict = combine_two_dict(output_dict, result)
        html_info_dict = dict_mapping_triedTree(self.info_dict)
        output_dict = combine_two_dict(output_dict, html_info_dict)
        if '工程招标信息' not in output_dict.keys():
            output_dict['工程招标信息'] = {}
        if '标段名称' not in output_dict['工程招标信息'].keys():
            try:
                zeta = re.findall("即(.*?)标段",self.html)[0]
                output_dict['工程招标信息']['标段名称'] = zeta
            except Exception as n:
                output_dict['工程招标信息']['标段名称'] = output_dict['工程基本信息']['项目名称']
                pass
        try:  # 防止多匹配
            a = ['a']
            if len(output_dict['未知']['未知电话']) > 1:
                a[0] = output_dict['未知']['未知电话'][0]
                output_dict['未知']['未知电话'] = a
        except Exception as f:
            pass
        output_dict=weizhi(output_dict)
        return output_dict

    def new_json_parse(self,response):  #用于解析json格式的网页
        h = re.compile(r'[{](.*?)"[}]', re.S) #定义提取大括号内内容的正则
        response = re.findall(h, response)
        response_list =list(response[0])
        response_list.append('"')
        response=''.join(response_list)
        response = '{'+response+'}'
        response=rf"""{response}"""
        try:   #如果json网页能正常转换
            response = json.loads(response)  # 转换成字典格式
            html = response['TENDERCONTENT']#得到指定的标签
            html = '<html> <body> '+html+' </body> </html>'
            html = rf"""{html}"""
            sel = etree.HTML(html)
            content_root_nodes = sel.xpath('//p')
            texts = []
            dr = re.compile(r'<[^>]+>', re.S)  # 构建去除所有的标签的正则
            dd = dr.sub('', html)
            dd2 = dd.replace('&nbsp;', '')  # 去除所有的&nbsp;
            dd = zhaobiaoneirong(dd2)
            if dd:
                pass       #12.26改动
                # texts.append(dd)
            else:
                pass
            # 遍历所有子节点，获取相应的文本
            #文本解析
            for node in content_root_nodes:
                node_text = node.xpath('string(.)')
                node_text = node_text.replace('\xa0','')
                node_text = node_text.replace('\t', '')
                texts.append(node_text)
            #加入表格中的文本
            table_list = sel.xpath('//table')
            for table in table_list:
                table_text = table.xpath('string(.)')
                table_text = table_text.replace('\xa0', '')
                texts.append(table_text)
            clean_texts = []
            # 清理文本中的一些空几个，不可见字符，以及加载关键字中间的空格
            for text in texts:
                text = replace_punctuation(text.strip())
                clean_texts.append(text)
            # 创建状态机
            machine = InfoMachine(self.base_pattern)
            # 执行状态机，解析整个文本
            output_dict = machine.run_list(clean_texts)

            #表格解析
            select = Selector(text=html)
            tables = get_all_tables(select)
            for table in tables:
                result = common_table_extrator(table)
                output_dict = combine_two_dict(output_dict, result)
            html_info_dict = dict_mapping_triedTree(self.info_dict)
            output_dict = combine_two_dict(output_dict, html_info_dict)

            #最后加工
            if '工程基本信息' not in output_dict.keys():
                output_dict['工程基本信息']={}
            if '工程招标信息' not in output_dict.keys():
                output_dict['工程招标信息']={}
            if '招标人信息名称' not in output_dict['工程招标信息'].keys():
                try:
                    c=['c']
                    c[0] = re.findall("联系方式(.*?)其他|联系方式(.*)", dd2)[0]
                    output_dict['工程招标信息']['招标人信息名称'] =c
                except Exception as b:
                    pass
            output_dict['工程基本信息']['项目名称'] = find_project_name(response['BNNAME'])
            output_dict['工程招标信息']['标段名称'] = response['PARAGRAPHNAME']
            output_dict['公告标题'] = response['BNNAME']
            try:  #防止多匹配
                a=['a']
                if len(output_dict['工程招标信息']['招标代理机构地址'])>1:
                    a[0] = output_dict['工程招标信息']['招标代理机构地址'][0]
                    output_dict['工程招标信息']['招标代理机构地址'] = a
            except Exception as f:
                pass
            try:  #防止多匹配
                b=['b']
                if len(output_dict['工程招标信息']['招标代理机构电话'])>1:
                    b[0] = output_dict['工程招标信息']['招标代理机构电话'][0]
                    output_dict['工程招标信息']['招标代理机构电话'] = b
            except Exception as f:
                pass
            output_dict=check_repeat(output_dict)
            return output_dict

        except Exception as wrong:  #网页无法转换，直接跳过
            print(wrong)

def weizhi(output_dict):   #用于解决未知的联系人或电话中包含代理的情况
    try:
        for i in output_dict['未知']['未知电话']:
            if '代理' in i:
                x = i.split('、',1)
                for a in x :
                    if '代理' in a:
                        z=['z']
                        z[0]=a
                        output_dict["工程招标信息"]["招标代理机构电话"] = z
                    else:
                        z = ['z']
                        z[0] = a
                        output_dict["工程招标信息"]["招标人信息电话"] = z
                del output_dict['未知']['未知电话']
            else:
                pass

        for q in output_dict['未知']['未知联系人']:
            if '代理' in q:
                x = q.split('、',1)
                for q in x :
                    if '代理' in q:
                        z = ['z']
                        z[0] = q
                        output_dict["工程招标信息"]["招标代理机构联系人"] = z
                    else:
                        z = ['z']
                        z[0] = q
                        output_dict["工程招标信息"]["招标人信息联系人"] = z
                del output_dict['未知']['未知联系人']
            else:
                pass
    except Exception as q:
        pass
    return output_dict







def find_project_name(gonggao_name):  #在取得项目名称时，遇如下非工程关键字，则保留项目完整名称
    a=['检测','代理','评估','监理','设计','评定','研究']
    for b in a :
        if b in gonggao_name:
            if '招标公告' in gonggao_name:
                project_name = re.findall("(.*?)招标公告",gonggao_name)[0]
                return project_name
            else:
                project_name = gonggao_name
                return project_name
        else:
            pass

    if'招标公告' in gonggao_name:
        if '项目' in gonggao_name and '工程'in gonggao_name:
            project_name = re.findall("(.*?)项目",gonggao_name)[0]+'项目'
        elif '项目' in gonggao_name and '工程' not in gonggao_name:
            project_name = re.findall("(.*?)项目", gonggao_name)[0] +'项目'
        elif '项目' not in gonggao_name and '工程' in gonggao_name:
            project_name = re.findall("(.*?)工程", gonggao_name)[0] + '工程'
        else:
            project_name  = gonggao_name.replace('招标公告','')
    elif '招标公告' not in gonggao_name:
        if '项目' in gonggao_name and '工程'in gonggao_name:
            project_name = re.findall("(.*?)项目",gonggao_name)[0]+'项目'
        elif '项目' in gonggao_name and '工程' not in gonggao_name:
            project_name = re.findall("(.*?)项目", gonggao_name)[0] +'项目'
        elif '项目' not in gonggao_name and '工程' in gonggao_name:
            project_name = re.findall("(.*?)工程", gonggao_name)[0] + '工程'
        else:
            project_name = gonggao_name
    return project_name


def zhaobiaoneirong(text):  #限定招标内容的解析范围
    try:
        first = ['.?.?.?招标范围和计划工期', '.?.?.?项目概况与招标范围', '.?.?.?招标范围和工作周期', '.?.?.?招标内容', '.?.?.?招标范围', '.?.?.?项目概况',
                 '.?.?.?采购说明', '.?.?.?项目概况及招标范围'
                 ]

        second = ['.?.?.?投标人资格要求', '.?.?.?投标人的合格条件', '.?.?.?企业条件', '.?.?.?投标人要求', '.?.?.?投标人资格、能力、信誉要求',
                  '.?.?.?本次招标对投标人资格条件要求如下', '.?.?.?企业条件', '.?.?.?报名条件', '.?.?.?本项目对投标人资格条件要求如下',
                  '.?.?.?投标资格要求', '.?.?.?招标条件', '.?.?.?凡满足下列条件的企业','投标人合格条件'
            , '(二)研究内容']
        for a in first:  # 提取招标内容
            for b in second:
                re_message = a + "(.*?)" + b
                message = re.findall(re_message, text)
                if len(message)>0:
                    message = message[0]
                    break
                else:
                    pass
            else:
                continue
            break
        return message
    except Exception as a:
        pass


def check_repeat(output_dict): #在输出前删除列表中重复的数据
    realfirstlist = []
    realsecondlist = []
    for k, v in output_dict.items():
        if type(v) == dict:
            realfirstlist.append(k)
            realsecondlist.append([i for i in output_dict[k].keys()])
    for k, v in zip(realfirstlist, realsecondlist):
        if len(v)!=0 :
            ##一级目录为空
            for i in v:
                content = output_dict[k][i]
                if type(content)== list:
                    if len(content)>1:
                        if content[0] == content[1]:
                            del content[1]
                            output_dict[k][i] = content
                else:
                    pass
    return output_dict

def replace(html):
    no_need =['网址','联系人','地址','传真','联系电话','电话','邮箱']

    for i in no_need:
        a= '('+i
        b= '（'+i
        if a or b in html:
            html = html.replace(a, '不要'+i)
            html = html.replace(b, '不要'+i)
    if '；邮箱：' in html:
        html = html.replace('；邮箱：','不要:')
    if '，联系方式：' or '。联系方式：' in html:
        html = html.replace('，联系方式：', '不要:')
        html = html.replace('。联系方式：', '不要:')
    if '，联系人：' or '。联系人：' in html:
        html = html.replace('，联系人：', '不要:')
        html = html.replace('。联系人：', '不要:')


    return html


if __name__ == '__main__':
    info_dict = {}
    for root, dirs, files, in os.walk('../../../demo_html/1.11'):
        for i,name in enumerate(files):
            if "init" not in name:
                print(f"\033[32m{i+1}=============={name}\033[0m")
                with open(f'../../../demo_html/1.11/{name}', 'r', encoding='utf-8') as fr:
                    html = fr.read()
                info_dict['html'] = html
                # info_dict['公告类型'] = "招标公告"  # "中标结果公告"
                obj = JiangSuShengGongLuShuiLuJianSheShiChangXinYongXinXiFuWuXiTong(info_dict)
                result = obj.start_parse()
                pprint(result)
