# -*- coding: utf-8 -*-
from pprint import pprint

from spidertools.utils.xpath_utils import get_alltext
from spidertools.utils.text_utils import clean_text
from spidertools.utils.snippets import combine_two_dict
from regular_matching_rules import get_keywordTredTree_instance
import re
from enum import Enum
import numpy as np
from table_info_extract import dict_mapping_triedTree,list_mapping_triedTree
from info_fsm import InfoMachine
from scrapy.selector import Selector
from spidertools.utils.text_utils import replace_punctuation



def get_first_trs(table_node,pattern = './*',deep_len = 0):
    nodes = table_node.xpath(pattern)
    found_tr = False
    for node in nodes:
        if node.root.tag == 'tr':
            found_tr = True
            break

    if found_tr:
        pattern = pattern[:-2] + '/tr'
        nodes = table_node.xpath(pattern)
    else:
        # 防止无限嵌套
        if deep_len < 3:
            deep_len += 1
            nodes =  get_first_trs(table_node,pattern+'/*',deep_len)
    return nodes

class tableModelEnum(Enum):
    model_one = 0
    model_two = 1
    model_three = 2
    model_four=3


class BaseTableMode(object):
    def __init__(self,mode):
        self.mode = mode

    @staticmethod
    def get_tr_parsed_value(tr_node):
        '''
        将tr下面的td里面的内容转换为key,value形式
        :param tr_node:
        :return:
        '''
        triedTree = get_keywordTredTree_instance()
        td_nodes = tr_node.xpath("./*")
        td_nodes = [node for node in td_nodes if node.root.tag == 'td' or node.root.tag == 'th']
        td_node_texts = [get_alltext(td_node) for td_node in td_nodes]
        td_node_texts = [clean_text(text) for text in td_node_texts]

        td_types = []
        td_values = []

        for text in td_node_texts:
            type = ""
            value = ""
            if text == "":
                td_types.append(type)
                td_values.append(value)
                continue
            keywords, types, end_positions = triedTree.process(text)

            value = text
            if len(keywords):
                key_regex = '^%s(\(.*\)){0,1}(:{0,1})' % keywords[0]
                match = re.match(key_regex, text)
                if match:
                    match_result = match[0]
                    if text == match_result:
                        type = "table_key"
                        value = keywords[0]
                    elif ":" in match_result:
                        type = "normal_text"
                    else:
                        type = ''

            td_types.append(type)
            td_values.append(value)
        return td_types, td_values



class  CommonTableModeTwo(BaseTableMode):
    '''
    通用表格类型2转换类，
    _____________________________________________________________________________________
    |中标候选人名称	|中国建筑第八工程局有限公司	|中建三局集团有限公司	|江苏省建筑工程集团有限公司|
    |企业资质等级	    |市政公用工程特级	        |市政公用工程一级	    |市政公用工程一级        |
    '''
    def __init__(self,mode):
        super(CommonTableModeTwo,self).__init__(mode)
        self.td_nums = 0
        self.result = {}


    # def get_result(self):
    #     output_list = []
    #     result_keys = self.result.keys()
    #     result_values = [self.result[key] for key in result_keys]
    #     trans_result_values = np.array(result_values).transpose().tolist()
    #
    #     for item in trans_result_values:
    #         tmp_result = {}
    #         for key,value in zip(result_keys,item):
    #             tmp_result[key] = value
    #         output_list.append(tmp_result)
    #     return output_list


    def get_result(self):
        first_fields = []
        first_fields_weizhi = []
        output_dict_list = []
        output_dict_list_weizhi = []
        result_keys = self.result.keys()
        result_values = [self.result[key] for key in result_keys]
        trans_result_values = np.array(result_values).transpose().tolist()

        for item in trans_result_values:
            output_=[]
            for key,value in zip(result_keys,item):
                key_value = key + ":" + value
                output_.append(key_value)
            # 执行状态机，解析整个文本
            machine = InfoMachine(base_regex='%s:\s*(.*)')
            output_dict = machine.run_list(output_)
            for first_field, first_field_content in output_dict.items():
                if first_field == "未知":
                    first_fields_weizhi.append(first_field)
                    output_dict_list_weizhi.append(first_field_content)
                else:
                    first_fields.append(first_field)
                    output_dict_list.append(first_field_content)
        if len(set(first_fields)) == 1 and len(set(first_fields_weizhi)) == 0:
            fin_output_dict = {first_fields[0]: output_dict_list}
        elif len(set(first_fields)) == 1 and len(set(first_fields_weizhi)) == 1:
            fin_output_dict = {first_fields[0]: output_dict_list}
            fin_output_dict["未知"] = output_dict_list_weizhi
        elif len(set(first_fields)) == 0 and len(set(first_fields_weizhi)) == 1:
            fin_output_dict={}
            fin_output_dict["未知"] = output_dict_list_weizhi
        else:
            fin_output_dict={}
        return fin_output_dict


    def reset_mode(self):
        self.td_nums = 0
        self.result = {}



    def check_tds_ok(self,td_types):
        check_ok = False
        if td_types[0] == "table_key":
            check_ok = True
            if self.td_nums == 0:
                self.td_nums = len(td_types)
            elif self.td_nums != len(td_types):
                check_ok = False
        return check_ok


    def parse_single_tr(self, td_values):
        result = {}
        key = td_values[0]
        result[key] = td_values[1:]
        return result

    def parse_table(self,table_node):
        tr_nodes = get_first_trs(table_node)
        for current_tr in tr_nodes:
            td_types, td_values = self.get_tr_parsed_value(current_tr)
            if self.check_tds_ok(td_types):
                tr_result = self.parse_single_tr(td_values)
                self.result = combine_two_dict(self.result,tr_result)



class  CommonTableModeOne(BaseTableMode):
    '''
    通用表格类型1转换类，
    _____________________________________________________________________________________
    |项目编号	|11111                     |项目名称	|东太湖旅游度假区中山南路延伸段 |
    |项目名称	|东太湖旅游度假区中山南路延伸段 |
    '''
    def __init__(self,mode):
        super(CommonTableModeOne,self).__init__(mode)
        self.result = {}
        self._result = []


    def get_result(self):
        # 执行状态机，解析整个文本
        machine = InfoMachine(base_regex='%s:\s*(.*)')
        _result=[]
        for key_value_list in self._result:
            for key_value in key_value_list:
                _result.append(key_value)
        print(_result)
        _result=["招标人:","名称:常熟市恒翔建设有限公司、江苏中康建设有限公司","招标代理单位:","联系地址:常熟市长江路134号"]
        output_dict = machine.run_list(_result)
        return output_dict

    def reset_mode(self):
        self.result = {}
        self._result = []



    def check_tds_ok(self,td_types):
        check_ok = False
        table_key_count = td_types.count('table_key')
        if table_key_count!=0 and table_key_count >= int(len(td_types) / 2):
            check_ok = True
        return check_ok


    # def parse_single_tr(self, td_values):
    #     result = {}
    #     for index in range(int(len(td_values)/2)):
    #         result[td_values[index*2]] = td_values[index*2 + 1]
    #     return result
    def parse_single_tr(self,td_values):
        results=[]
        for index in range(int(len(td_values)/2)):
            key=td_values[index*2]
            value=td_values[index*2 + 1]
            results.append(key+":"+value)
        return results

    # def parse_table(self,table_node):
    #     tr_nodes = get_first_trs(table_node)
    #     for current_tr in tr_nodes:
    #         td_types, td_values = self.get_tr_parsed_value(current_tr)
    #         if self.check_tds_ok(td_types):
    #             tr_result = self.parse_single_tr(td_values)
    #             self.result = combine_two_dict(self.result,tr_result)
    def parse_table(self,table_node):
        tr_nodes = get_first_trs(table_node)
        for current_tr in tr_nodes:
            td_types, td_values = self.get_tr_parsed_value(current_tr)
            if self.check_tds_ok(td_types):
                tr_result = self.parse_single_tr(td_values)
                self._result.append(tr_result)
class  CommonTableModeFour(BaseTableMode):
    """sample"""
    def __init__(self,mode):
        super(CommonTableModeFour,self).__init__(mode)
        self.result = {}


    def get_result(self):
        # 执行状态机，解析整个文本
        machine = InfoMachine(base_regex='%s:\s*(.*)')
        _result=[]
        for key,value in self.result.items():
            if "工期" in key:
                j = 1
            _result.append(key+':'+value)
        output_dict = machine.run_list(_result)
        return output_dict

    def reset_mode(self):
        self.result = {}



    def check_tds_ok(self,td_types):
        check_ok = False
        table_key_count = td_types.count('table_key')
        if table_key_count!=0 and table_key_count >= int(len(td_types) / 2):
            check_ok = True
        return check_ok


    def parse_single_tr(self, td_values):
        result = {}
        for index in range(int(len(td_values)/2)):
            result[td_values[index*2]] = td_values[index*2 + 1]

        return result

    def parse_table(self,table_node):
        tr_nodes = get_first_trs(table_node)
        for current_tr in tr_nodes:
            td_types, td_values = self.get_tr_parsed_value(current_tr)
            if self.check_tds_ok(td_types):
                tr_result = self.parse_single_tr(td_values)
                self.result = combine_two_dict(self.result,tr_result)

class  CommonTableModeThree(BaseTableMode):
    '''
    通用表格类型3转换类，
    _____________________________________________________________________________________
    |项目编号	|项目名称                     |... |
    |XXXXXX  	|东太湖旅游度假区中山南路延伸段   |... |
    '''

    def __init__(self, mode):
        super(CommonTableModeThree, self).__init__(mode)
        self.td_nums = 0
        self.found_keys = False
        self.result = {}


    # def get_result(self):
    #     output_list = []
    #     if 'values' in self.result:
    #         result_keys = self.result['keys']
    #         result_values = self.result['values']
    #
    #         for item in result_values:
    #             tmp_result = {}
    #             for key, value in zip(result_keys, item):
    #                 tmp_result[key] = value
    #             output_list.append(tmp_result)
    #     return output_list

    def get_result(self):
        first_fields = []
        first_fields_weizhi = []
        output_dict_list = []
        output_dict_list_weizhi = []
        if 'values' in self.result:
            result_keys = self.result['keys']
            result_values = self.result['values']

            for item in result_values:
                output_ = []
                for key, value in zip(result_keys, item):
                    key_value = key + ":" + value
                    output_.append(key_value)
                # 执行状态机，解析整个文本
                machine = InfoMachine(base_regex='%s:\s*(.*)')
                output_dict = machine.run_list(output_)
                for first_field, first_field_content in output_dict.items():
                    if first_field == "未知":
                        first_fields_weizhi.append(first_field)
                        output_dict_list_weizhi.append(first_field_content)
                    else:
                        first_fields.append(first_field)
                        output_dict_list.append(first_field_content)
        if len(set(first_fields)) == 1 and len(set(first_fields_weizhi)) == 0:
            fin_output_dict = {first_fields[0]: output_dict_list}
        elif len(set(first_fields)) == 1 and len(set(first_fields_weizhi)) == 1:
            fin_output_dict = {first_fields[0]: output_dict_list}
            fin_output_dict["未知"] = output_dict_list_weizhi
        elif len(set(first_fields)) == 0 and len(set(first_fields_weizhi)) == 1:
            fin_output_dict={}
            fin_output_dict["未知"] = output_dict_list_weizhi
        else:
            fin_output_dict={}
        return fin_output_dict


    def reset_mode(self):
        self.found_keys =False
        self.td_nums = 0
        self.result = {}

    def check_tds_ok(self, td_types):
        check_ok = False
        tds_type = ""
        table_key_count = td_types.count('table_key')
        if table_key_count == len(td_types):
            self.td_nums = table_key_count
            check_ok = True
            tds_type = "table_key_tr"
        elif table_key_count <= int(len(td_types)) and len(td_types) == self.td_nums:
            check_ok = True
            tds_type = "table_value_tr"
        return check_ok,tds_type

    def parse_single_tr(self, td_values,tr_type):
        if tr_type == "table_key_tr":
            self.result["keys"] = td_values
        elif tr_type == "table_value_tr":
            if 'values' not in self.result:
                self.result['values'] = []
            self.result['values'].append(td_values)

    def parse_table(self, table_node):
        tr_nodes = get_first_trs(table_node)
        for current_tr in tr_nodes:
            td_types, td_values = self.get_tr_parsed_value(current_tr)
            td_stats,tr_type = self.check_tds_ok(td_types)
            if td_stats:
                self.parse_single_tr(td_values,tr_type)

def judge_standard_table(label_trnodes):
    """
    :param table_node:
    :return:
    :fyi:判断是否为标准表格
    """
    numslist = [len(i) for i in label_trnodes]
    if len(set(numslist))==1:
        return True
    else:
        mode_list=[]
        for label_trnode in label_trnodes:
            text="<table><tr>{}</tr></table>".format("".join(label_trnode))
            sel=Selector(text=text)
            mode=get_table_mode_type(sel)
            mode_list.append(mode)
        if len(set(mode_list))==1:
            return True
        else:
            return False
def judge_nbsp(label_notrnodes):
    # "&nbsp"=="\xa0"
    first_y_notrnodes = []
    first_x_notrnodes = []
    # y 第一个元素
    for n_labellist in label_notrnodes:
        if len(n_labellist) > 0:
            first_y_notrnodes.append(n_labellist[0])
    # x 第一行元素
    if len(label_notrnodes) > 0:
        first_x_notrnodes = label_notrnodes[0]

    first_x_notrnodes_set=list(set(first_x_notrnodes))
    first_y_notrnodes_set=list(set(first_y_notrnodes))
    if (first_x_notrnodes_set==["\xa0"] or first_y_notrnodes_set==["\xa0"]):
        return True
    else:
        return False


def _process_td_data(table_node):
    """
    :param table_node: 去除table 和content=""
    :return:
    """
    tr_nodes = get_first_trs(table_node)
    label_trnodes = []
    label_notrnodes = []
    for tr in tr_nodes:
        label_trnode = tr.xpath(".//td|.//th").extract()
        label_trnode_content = tr.xpath(".//td//text()").extract()
        label_trnode_ = "".join(label_trnode)
        if "<table" not in label_trnode_ and "table>" not in label_trnode_ and len(label_trnode_content) and not list(
                set(label_trnode_content)) == [" "] and not list( set(label_trnode_content))==["\xa0"]:
            label_notrnodes.append(label_trnode_content)
            label_trnodes.append(label_trnode)
    return label_trnodes,label_notrnodes


def _move_nbsp_table(label_trnodes,label_notrnodes):
    """
    :param table_node:
    :return:
    :fyi:0.先判断是否是正规的表格；
        1.首n行是&nbsp；2.首n列是&nbsp；3.首n行，首n列都&nbsp；
        ps。去tabla_node 中的table。
        1.zip（td中的值，td标签）如果td中的值都为nbsp；保留td原始标签；
        2.zip（td中的值，td标签）获得截断；
        3.复合1，2中的情况；
    """
    # "&nbsp"=="\xa0"
    first_y_notrnodes = []
    first_x_notrnodes = []
    # y 第一个元素
    for n_labellist in label_notrnodes:
        if len(n_labellist) > 0:
            first_y_notrnodes.append(n_labellist[0])
    # x 第一行元素
    if len(label_notrnodes) > 0:
        first_x_notrnodes = label_notrnodes[0]

    first_x_notrnodes_set = list(set(first_x_notrnodes))
    first_y_notrnodes_set = list(set(first_y_notrnodes))

    if first_x_notrnodes_set == ["\xa0"] and not first_y_notrnodes_set == ["\xa0"]:
        tr_contentlist_fittler = []
        for yes_label, no_label in zip(label_trnodes, label_notrnodes):
            if list(set(no_label)) != ["\xa0"]:
                tr_contentlist_fittler.append(yes_label)
        return tr_contentlist_fittler
    elif not first_x_notrnodes_set == ["\xa0"] and first_y_notrnodes_set == ["\xa0"]:
        labels_fittler = []
        tr_contentlist_fittler = []
        # 获取列数据
        count = 0
        for contents in zip(*label_notrnodes):
            if list(set(contents)) == ["\xa0"]:
                count += 1
        for labels in label_trnodes:
            labels_fittler.append(labels[count:])
        for label_fittler in labels_fittler:
            tr_contentlist_fittler.append(label_fittler)
        return tr_contentlist_fittler
    elif first_x_notrnodes_set== ["\xa0"] and first_y_notrnodes_set == ["\xa0"]:
        ##先去除x
        label_trnodes1 = []
        label_notrnodes1 = []
        for yes_label, no_label in zip(label_trnodes, label_notrnodes):
            if list(set(no_label)) != ["\xa0"]:
                label_trnodes1.append(yes_label)
                label_notrnodes1.append(no_label)
        #去除y
        tr_contentlist_fittler = []
        #获取列数据 \xa0
        count=0
        for contents in zip(*label_notrnodes1):
            if list(set(contents))==["\xa0"]:
               count+=1
        for labels in label_trnodes1:
            tr_contentlist_fittler.append(labels[count:])
        return tr_contentlist_fittler

def _become_mode_texts(groups_texts_mode_one):
    texts_one_list = []
    for groups_text_mode_one in groups_texts_mode_one:
        _groups_texts_mode_one = "<tr>{}</tr>".format("".join(groups_text_mode_one))
        _groups_texts_mode_one = re.sub(r'rowspan="\d*"', "", _groups_texts_mode_one)
        texts_one_list.append(_groups_texts_mode_one)
    texts_one = "<table><tbody>{}</tbody></table>".format("".join(texts_one_list))
    sel=Selector(text=texts_one)
    return sel

def _process_standard_table(label_trnodes1):
    tr_contentlist_fittler = []
    for label_fittler in label_trnodes1:
        labelcontent = "<tr>{}</tr>".format("".join(label_fittler))
        tr_contentlist_fittler.append(labelcontent)
    texts = "<table><tbody>{}</tbody></table>".format("".join(tr_contentlist_fittler))
    sel = [Selector(text=texts)]
    return sel
def _process_mode_three_none(groups_texts_mode_three,groups_texts_mode_none):
    groups_texts_mode_three_tds=groups_texts_mode_three[0]
    table_text = "<table><tbody><tr>{}</tr></tbody></table>".format("".join(groups_texts_mode_three_tds))
    sel = Selector(text=table_text)
    tr_node = get_first_trs(sel)
    label_trnode = tr_node.xpath(".//td").extract()
    groups_texts_mode_three_length=len(label_trnode)
    groups_texts_mode_none_fittler=[]
    for text_mode_none in groups_texts_mode_none:
        table_text = "<table><tbody><tr>{}</tr></tbody></table>".format("".join(text_mode_none))
        sel = Selector(text=table_text)
        tr_node = get_first_trs(sel)
        td_types, td_values = BaseTableMode.get_tr_parsed_value(tr_node)
        if len(td_values)==groups_texts_mode_three_length and list(set(td_types))==[""]:
            groups_texts_mode_none_fittler.append("".join(text_mode_none))
    groups_texts_mode_three=groups_texts_mode_three+groups_texts_mode_none_fittler
    return groups_texts_mode_three


def _process_not_standard_table(label_trnodes1):
    groups_texts_mode_one = []
    groups_texts_mode_two = []
    groups_texts_mode_three = []
    groups_texts_mode_none=[]
    numslist = [len(i) for i in label_trnodes1]
    """分组"""
    categarys = list(set(numslist))
    for categary in categarys:
        for index, num in enumerate(numslist):
            if num == categary:
                text = "".join(label_trnodes1[index])
                table_text = "<table><tbody><tr>{}</tr></tbody></table>".format(text)
                sel = Selector(text=table_text)
                mode = get_table_mode_type(sel)
                if mode == tableModelEnum.model_three :
                    groups_texts_mode_three.append(text)
                if mode=="":
                    groups_texts_mode_none.append(text)
                if mode == tableModelEnum.model_one:
                    groups_texts_mode_one.append(text)
                elif mode == tableModelEnum.model_two:
                    groups_texts_mode_two.append(text)
                elif mode == tableModelEnum.model_four:
                    textlist=sel.xpath(".//td").extract()[1:]
                    text="".join(textlist)
                    groups_texts_mode_one.append(text)
    if len(groups_texts_mode_three)==1 and len(groups_texts_mode_none)>0:
        groups_texts_mode_three=_process_mode_three_none(groups_texts_mode_three,groups_texts_mode_none)
    else:
        groups_texts_mode_three=[]
    groups_texts_modes=[groups_texts_mode_one,groups_texts_mode_two,groups_texts_mode_three]
    return groups_texts_modes

def _process_table(table_node):
    label_trnodes,label_notrnodes=_process_td_data(table_node)
    if judge_nbsp(label_notrnodes):
        label_trnodes=_move_nbsp_table(label_trnodes,label_notrnodes)
    else:
        label_trnodes=label_trnodes
    label_trnodes1=[]
    label_notrnodes1=[]
    for label_trnode,label_notrnode in zip(label_trnodes,label_notrnodes):
        if len(label_trnode)!=1:
            label_trnodes1.append(label_trnode)
        else:
            label_notrnodes1.append("".join(label_notrnode))
    if judge_standard_table(label_trnodes1):
        sel=_process_standard_table(label_trnodes1)
        return sel,label_notrnodes1
    else:
        sels=[]
        groups_texts_modes=_process_not_standard_table(label_trnodes1)
        for groups_texts_mode in groups_texts_modes:
            if groups_texts_mode:
                sel = _become_mode_texts(groups_texts_mode)
                sels.append(sel)
        return sels,label_notrnodes1
def _process_results(_results):
    """
    四种模式结果s，模式1、2、3、加表格td=1，经过状态机结果
    :param results:
    :return:
    """
    results=[]
    for result in _results:
        if result:
            results.append(result)
        else:pass
    if len(results)==1:
        result=results[0]
    elif len(results)==2:
        result=combine_two_dict(results[0],results[1])
    elif len(results)==3:
        result1=combine_two_dict(results[0],results[1])
        result=combine_two_dict(result1,results[2])
    elif len(results)==4:
        result1=combine_two_dict(results[0],results[1])
        result2=combine_two_dict(results[2],results[3])
        result = combine_two_dict(result2, result1)
    else:
        result={}
    return result
def common_table_extrator1(table_node):
    '''
    通用表格转换模板
    :param table_node:
    :return:
    '''
    table_mode = get_table_mode_type(table_node)
    if table_mode != "":
        if table_mode == tableModelEnum.model_two:
            convert_table_obj = CommonTableModeTwo(table_mode)
            convert_table_obj.parse_table(table_node)
            result = convert_table_obj.get_result()
            if type(result) == dict:
                result = dict_mapping_triedTree(result)
            elif type(result) == list:
                result = list_mapping_triedTree(result)
            else:
                result = {}
        elif table_mode == tableModelEnum.model_one:
            convert_table_obj = CommonTableModeOne(table_mode)
            convert_table_obj.parse_table(table_node)
            result = convert_table_obj.get_result()
            return result
        elif table_mode == tableModelEnum.model_three:
            convert_table_obj = CommonTableModeThree(table_mode)
            convert_table_obj.parse_table(table_node)
            result = convert_table_obj.get_result()
            if type(result) == dict:
                result = dict_mapping_triedTree(result)
            elif type(result) == list:
                result = list_mapping_triedTree(result)
            else:
                result = {}

    else:
        result = {}
    return result
def common_table_extrator(table_node):
    '''
    通用表格转换模板
    :param table_node:
    :return:
    '''
    results=[]
    table_nodes_list,label_notrnodes1=_process_table(table_node)
    if label_notrnodes1:
        machine = InfoMachine(base_regex='%s:\s*(.*)')
        clean_texts = []
        # 清理文本中的一些空几个，不可见字符，以及加载关键字中间的空格
        for text in label_notrnodes1:
            text = replace_punctuation(text.strip().replace(" ",""))
            clean_texts.append(text)
        label_notrnodes1_result = machine.run_list(clean_texts)
    else:
        label_notrnodes1_result={}

    results.append(label_notrnodes1_result)
    for table_node in table_nodes_list:
        table_mode = get_table_mode_type(table_node)
        if table_mode != "":
            if table_mode == tableModelEnum.model_two:
                convert_table_obj = CommonTableModeTwo(table_mode)
                convert_table_obj.parse_table(table_node)
                result = convert_table_obj.get_result()
                # if type(result) == dict:
                #     result = dict_mapping_triedTree(result)
                # elif type(result) == list:
                #     result = list_mapping_triedTree(result)
                # else:
                #     result = {}
                results.append(result)
            elif table_mode == tableModelEnum.model_one:
                convert_table_obj = CommonTableModeOne(table_mode)
                convert_table_obj.parse_table(table_node)
                result = convert_table_obj.get_result()
                results.append(result)
            elif table_mode == tableModelEnum.model_three:
                convert_table_obj = CommonTableModeThree(table_mode)
                convert_table_obj.parse_table(table_node)
                result = convert_table_obj.get_result()
                # if type(result) == dict:
                #     result = dict_mapping_triedTree(result)
                # elif type(result) == list:
                #     result = list_mapping_triedTree(result)
                # else:
                #     result = {}
                results.append(result)
        else:
            result = {}
            results.append(result)

    result=_process_results(results)
    return result
def get_table_mode_type(table_node):
    '''
    判断一下，表格是什么类型的
    :param table_node:
    :return:
    '''
    tr_nodes = get_first_trs(table_node)
    table_mode = ""
    for current_tr in tr_nodes:
        td_types, td_values = BaseTableMode.get_tr_parsed_value(current_tr)
        if 'table_key' not in td_types:
            continue
        table_key_count = td_types.count('table_key')
        if table_key_count == round(len(td_types) / 2):
            table_mode = tableModelEnum.model_one
        elif td_types[0] == 'table_key' and table_key_count == 1:
            table_mode = tableModelEnum.model_two
        elif table_key_count == len(td_types):
            table_mode = tableModelEnum.model_three
        elif table_key_count*2-len(td_types)==1:
            table_mode = tableModelEnum.model_four
        else:
            table_mode = ""

        if table_mode != "":
            break

    return table_mode


if __name__ == '__main__':
    # test_html = ""
    # test_file = r'F:\工作相关文档\爬虫相关\company_info_extrator\demo_html\table_model_one.html'
    # with open(test_file,'r',encoding='utf-8') as fread:
    #     test_html = fread.read()
    #
    #
    #
    #
    # sel = Selector(text=test_html)
    # common_table_extrator(sel.xpath("//table")[0])
    # test_html="""<table id="_Sheet1_2_0" cellpadding="0" cellspacing="0" style="table-layout: fixed;font-family:SimSun;font-size:9pt;color:#000000;border-collapse:collapse;" border="0" width="1201">	<tr height="0px" style="font-size: 0px;line-height:0px;">		<td width="345px" style="border-left:#0000 1px solid;border-right:#0000  1px solid;"> </td>		<td width="299px" style="border-right:#0000  1px solid;"> </td>		<td width="276px" style="border-right:#0000  1px solid;"> </td>		<td width="281px" style="border-right:#0000 1px solid;"> </td>	</tr>	<tr height="24px">		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第一中标候选人</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第二中标候选人</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第三中标候选人</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标候选人名称</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">南京平川工程项目管理有限公司</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">南京第一建设事务所有限责任公司</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">江苏大洲工程项目管理有限公司</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标报价(元)</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人姓名</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">梅六宏</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">邵小刚</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">施成忠</td>	</tr>	<tr height="25px">		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">工期(天)</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td>	</tr>	<tr height="25px">		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">质量要求</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人证书编号</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">32014170</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">32018806</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">32012201</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标人业绩</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人业绩</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td>	</tr>	</table>"""
    test_html="""<table id="_Sheet1" align="center" cellpadding="0" cellspacing="0" style="table-layout: fixed;font-family:宋体;font-size:9pt;color:#000000;border-collapse:collapse;" border="0" width="842">	<tbody><tr height="0px" style="font-size: 0px;line-height:0px;">		<td width="173px" style="border-left:#0000 1px solid;border-right:#0000  1px solid;">&nbsp;</td>		<td width="149px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="88px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="98px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="95px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="88px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="74px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="77px" style="border-right:#0000 1px solid;">&nbsp;</td>	</tr>	<tr>		<td style="border-bottom:#d1e6fa 1px solid;font-size:14pt;color:#ff0000;font-weight:bold;padding:2px;text-align:center" colspan="8">2019-2020年度镇江文旅集团部分小型建设项目镇江文旅集团2019年度招标代理服务框架招标的中标公告</td>	</tr>	<tr height="35px">		<td class="ClassBlue" style="text-align:center">项目编号:</td>		<td class="ClassWhite" colspan="7">ZJS2019061522</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">项目名称:</td>		<td class="ClassWhite" colspan="7">2019-2020年度镇江文旅集团部分小型建设项目</td>	</tr>	<tr height="35px">		<td class="ClassBlue" style="text-align:center">标段编号:</td>		<td class="ClassWhite" colspan="7">ZJS2019061522-02</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">标段名称:</td>		<td class="ClassWhite" colspan="7">镇江文旅集团2019年度招标代理服务框架招标</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">招标人名称:</td>		<td class="ClassWhite" colspan="7">镇江文化旅游产业集团有限责任公司</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">项目类型:</td>		<td class="ClassWhite" colspan="7">		</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">招标方式:</td>		<td class="ClassWhite" colspan="7">公开招标		</td>	</tr>	<tr height="53px">		<td class="ClassBlue" style="text-align:center"><br>序号</td>		<td class="ClassBlue" style="text-align:center">中标人名称</td>		<td class="ClassBlue" style="text-align:center">项目负责人姓名</td>		<td class="ClassBlue" style="text-align:center">项目负责人资质等级</td>		<td class="ClassBlue" style="text-align:center">项目负责人注册证号</td>		<td class="ClassBlue" style="text-align:center">中标价(元)</td>		<td class="ClassBlue" style="text-align:center">中标工期(日历天)</td>		<td class="ClassBlue" style="text-align:center">质量标准</td>	</tr>	<tr>		<td class="ClassWhite" style="text-align:center">1</td>		<td class="ClassWhite">镇江市华辰招标代理咨询有限公司</td>		<td class="ClassWhite">瞿志钢</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>	<tr>		<td class="ClassWhite" style="text-align:center">2</td>		<td class="ClassWhite">江苏大洲工程项目管理有限公司</td>		<td class="ClassWhite">王立冈</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>	<tr>		<td class="ClassWhite" style="text-align:center">3</td>		<td class="ClassWhite">江苏唯诚建设咨询有限公司</td>		<td class="ClassWhite">陈刚</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">定标时间：</td>		<td class="ClassWhite" colspan="7">&nbsp;</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">工程地点：</td>		<td class="ClassWhite" colspan="7">镇江市</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">评标委员会成员:</td>		<td class="ClassWhite" colspan="7">李春红,袁金兰,卢小娟,郭方杰,朱美</td>	</tr>	<tr>		<td class="ClassBlue" style="text-align:center">招标人定标原因及依据：</td>		<td class="ClassWhite" colspan="7">根据招标文件的评标、定标方法</td>	</tr>	<tr>		<td class="ClassBlue" style="text-align:center">中标结果公告发布日期：</td>		<td class="ClassWhite" colspan="7">2019年07月17日</td>	</tr>	</tbody></table>"""

    # test_html="""<table><tbody><tr><td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第一中标候选人</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第二中标候选人</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第三中标候选人</td></tr><tr><td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标候选人名称</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">南京平川工程项目管理有限公司</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">南京第一建设事务所有限责任公司</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">江苏大洲工程项目管理有限公司</td></tr><tr><td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标报价(元)</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td></tr><tr><td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人姓名</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">梅六宏</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">邵小刚</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">施成忠</td></tr><tr><td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">工期(天)</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td></tr><tr><td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">质量要求</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td></tr><tr><td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人证书编号</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">32014170</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">32018806</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">32012201</td></tr><tr><td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标人业绩</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td></tr><tr><td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人业绩</td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td><td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center"> </td></tr></tbody></table>"""

    # test_html="""<table><tbody>
    #             <tr height="53px">		<td class="ClassBlue" style="text-align:center">序号</td>		<td class="ClassBlue" style="text-align:center">中标人名称</td>		<td class="ClassBlue" style="text-align:center">项目负责人姓名</td>		<td class="ClassBlue" style="text-align:center">项目负责人资质等级</td>		<td class="ClassBlue" style="text-align:center">项目负责人注册证号</td>		<td class="ClassBlue" style="text-align:center">中标价(元)</td>		<td class="ClassBlue" style="text-align:center">中标工期(日历天)</td>		<td class="ClassBlue" style="text-align:center">质量标准</td>	</tr>
    #             <tr>		<td class="ClassWhite" style="text-align:center">1</td>		<td class="ClassWhite">镇江市华辰招标代理咨询有限公司</td>		<td class="ClassWhite">瞿志钢</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>
    #             <tr>		<td class="ClassWhite" style="text-align:center">2</td>		<td class="ClassWhite">江苏大洲工程项目管理有限公司</td>		<td class="ClassWhite">王立冈</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>
    #             <tr>		<td class="ClassWhite" style="text-align:center">3</td>		<td class="ClassWhite">江苏唯诚建设咨询有限公司</td>		<td class="ClassWhite">陈刚</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>
    #             </tbody></table>"""

    #     test_html="""<table><tbody>
    # <tr height="53px">		<td class="ClassBlue" style="text-align:center">序号</td>		<td class="ClassBlue" style="text-align:center">中标人名称</td>		<td class="ClassBlue" style="text-align:center">项目负责人姓名</td>		<td class="ClassBlue" style="text-align:center">项目负责人资质等级</td>		<td class="ClassBlue" style="text-align:center">项目负责人注册证号</td>		<td class="ClassBlue" style="text-align:center">中标价(元)</td>		<td class="ClassBlue" style="text-align:center">中标工期(日历天)</td>		<td class="ClassBlue" style="text-align:center">质量标准</td>	</tr>
    # <tr>		<td class="ClassWhite" style="text-align:center">1</td>		<td class="ClassWhite">镇江市华辰招标代理咨询有限公司</td>		<td class="ClassWhite">瞿志钢</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>
    # </tbody></table>"""


    # test_html="""<table width="760"><tbody><tr class="firstRow" style="height: 21px;"><td width="72" style="padding: 0px 7px; border: 1px solid windowtext; border-image: none; background-color: transparent;"><p style="margin: 0px 0px 11px; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">招标人1</span></p></td><td width="176" style="border-width: 1px 1px 1px 0px; border-style: solid solid solid none; border-color: windowtext windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; border-image: none; background-color: transparent;"><p style="margin: 0px 0px 11px;"><span style="color: windowtext; line-height: 107%; font-family: 宋体; font-size: 14px;">泰州市海陵区交通建设服务中心</span></p></td><td width="104" style="border-width: 1px 1px 1px 0px; border-style: solid solid solid none; border-color: windowtext windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; border-image: none; background-color: transparent;"><p style="margin: 0px 0px 11px; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">招标代理机构</span></p></td><td width="257" style="border-width: 1px 1px 1px 0px; border-style: solid solid solid none; border-color: windowtext windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; border-image: none; background-color: transparent;"><p style="margin: 0px 0px 11px; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">江苏华强工程投资管理咨询有限公司</span></p></td></tr><tr style="height: 21px;"><td width="72" style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; border-image: none; background-color: transparent;"><p style="margin: 0px 0px 11px; text-align: center; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">地址</span></p></td><td width="176" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><p style="margin: 0px 0px 11px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">江苏省泰州市海陵区税务西街21号</span></p></td><td width="104" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><p style="margin: 0px 0px 11px; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">地址</span></p></td><td width="257" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><p style="margin: 0px 0px 11px; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">泰州市海陵南路179号华诚大厦B座9楼（华强代理）</span></p></td></tr><tr style="height: 21px;"><td width="72" style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; border-image: none; background-color: transparent;"><p style="margin: 0px 0px 11px; text-align: center; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">联系人</span></p></td><td width="176" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><p style="margin: 0px 0px 11px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">王先生</span></p></td><td width="104" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><p style="margin: 0px 0px 11px; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">联系人</span></p></td><td width="257" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><p style="margin: 0px 0px 11px; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">陈先生</span></p></td></tr><tr style="height: 29px;"><td width="72" style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; border-image: none; background-color: transparent;"><p style="margin: 0px 0px 11px; text-align: center; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">电话</span></p></td><td width="176" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><p style="margin: 0px 0px 11px; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">0523-80188087</span></p></td><td width="104" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><p style="margin: 0px 0px 11px; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">电话、传真</span></p></td><td width="257" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><p style="margin: 0px 0px 11px; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">0523-</span><span style="color: windowtext; font-family: 宋体; font-size: 14px;">86882663</span></p></td></tr><tr style="height: 21px;"><td width="72" style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; border-image: none; background-color: transparent;"><br></td><td width="176" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><br></td><td width="104" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><p style="margin: 0px 0px 11px; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">电子邮箱</span></p></td><td width="257" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><p style="margin: 0px 0px 11px; line-height: 27px;"><span style="color: windowtext; font-family: 宋体; font-size: 14px;">Hq86882663@163.com</span></p></td></tr></tbody></table>"""

    # test_html="""<html><head></head><body><table id="_Sheet1_2_0" cellpadding="0" cellspacing="0" style="table-layout: fixed;font-family:SimSun;font-size:9pt;color:#000000;border-collapse:collapse;" border="0" width="1201">	<tbody><tr height="0px" style="font-size: 0px;line-height:0px;">		<td width="345px" style="border-left:#0000 1px solid;border-right:#0000  1px solid;">&nbsp;</td>		<td width="299px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="276px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="281px" style="border-right:#0000 1px solid;">&nbsp;</td>	</tr>	<tr height="24px">		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第一中标候选人</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第二中标候选人</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第三中标候选人</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标候选人名称</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">南京平川工程项目管理有限公司</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">南京第一建设事务所有限责任公司</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">江苏大洲工程项目管理有限公司</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标报价(元)</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人姓名</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">梅六宏</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">邵小刚</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">施成忠</td>	</tr>	<tr height="25px">		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">工期(天)</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td>	</tr>	<tr height="25px">		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">质量要求</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>	</tr>		<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标人业绩</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人业绩</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>	</tr>	</tbody></table></body></html>"""

    # test_html="""<table id="_Sheet1_2_0" cellpadding="0" cellspacing="0" style="table-layout: fixed;font-family:SimSun;font-size:9pt;color:#000000;border-collapse:collapse;" border="0" width="1201">	<tbody><tr height="0px" style="font-size: 0px;line-height:0px;">		<td width="345px" style="border-left:#0000 1px solid;border-right:#0000  1px solid;">&nbsp;</td>		<td width="299px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="276px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="281px" style="border-right:#0000 1px solid;">&nbsp;</td>	</tr>	<tr height="24px">		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第一中标候选人</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第二中标候选人</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第三中标候选人</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标候选人名称</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">南京平川工程项目管理有限公司</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">南京第一建设事务所有限责任公司</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">江苏大洲工程项目管理有限公司</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标报价(元)</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人姓名</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">梅六宏</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">邵小刚</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">施成忠</td>	</tr>	<tr height="25px">		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">工期(天)</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td>	</tr>	<tr height="25px">		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">质量要求</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人证书编号</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">32014170</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">32018806</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">32012201</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标人业绩</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人业绩</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>	</tr>	</tbody></table>"""
    test_html="""<table id="_Sheet1" align="center" cellpadding="0" cellspacing="0" style="table-layout: fixed;font-family:宋体;font-size:9pt;color:#000000;border-collapse:collapse;" border="0" width="842">	<tbody><tr height="0px" style="font-size: 0px;line-height:0px;">		<td width="173px" style="border-left:#0000 1px solid;border-right:#0000  1px solid;">&nbsp;</td>		<td width="149px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="88px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="98px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="95px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="88px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="74px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="77px" style="border-right:#0000 1px solid;">&nbsp;</td>	</tr>	<tr>		<td style="border-bottom:#d1e6fa 1px solid;font-size:14pt;color:#ff0000;font-weight:bold;padding:2px;text-align:center" colspan="8">2019-2020年度镇江文旅集团部分小型建设项目镇江文旅集团2019年度招标代理服务框架招标的中标公告</td>	</tr>	<tr height="35px">		<td class="ClassBlue" style="text-align:center">项目编号:</td>		<td class="ClassWhite" colspan="7">ZJS2019061522</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">项目名称:</td>		<td class="ClassWhite" colspan="7">2019-2020年度镇江文旅集团部分小型建设项目</td>	</tr>	<tr height="35px">		<td class="ClassBlue" style="text-align:center">标段编号:</td>		<td class="ClassWhite" colspan="7">ZJS2019061522-02</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">标段名称:</td>		<td class="ClassWhite" colspan="7">镇江文旅集团2019年度招标代理服务框架招标</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">招标人名称:</td>		<td class="ClassWhite" colspan="7">镇江文化旅游产业集团有限责任公司</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">项目类型:</td>		<td class="ClassWhite" colspan="7">		</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">招标方式:</td>		<td class="ClassWhite" colspan="7">公开招标		</td>	</tr>	<tr height="53px">		<td class="ClassBlue" style="text-align:center"><br>序号</td>		<td class="ClassBlue" style="text-align:center">中标人名称</td>		<td class="ClassBlue" style="text-align:center">项目负责人姓名</td>		<td class="ClassBlue" style="text-align:center">项目负责人资质等级</td>		<td class="ClassBlue" style="text-align:center">项目负责人注册证号</td>		<td class="ClassBlue" style="text-align:center">中标价(元)</td>		<td class="ClassBlue" style="text-align:center">中标工期(日历天)</td>		<td class="ClassBlue" style="text-align:center">质量标准</td>	</tr>	<tr>		<td class="ClassWhite" style="text-align:center">1</td>		<td class="ClassWhite">镇江市华辰招标代理咨询有限公司</td>		<td class="ClassWhite">瞿志钢</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>	<tr>		<td class="ClassWhite" style="text-align:center">2</td>		<td class="ClassWhite">江苏大洲工程项目管理有限公司</td>		<td class="ClassWhite">王立冈</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>	<tr>		<td class="ClassWhite" style="text-align:center">3</td>		<td class="ClassWhite">江苏唯诚建设咨询有限公司</td>		<td class="ClassWhite">陈刚</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">定标时间：</td>		<td class="ClassWhite" colspan="7">&nbsp;</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">工程地点：</td>		<td class="ClassWhite" colspan="7">镇江市</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">评标委员会成员:</td>		<td class="ClassWhite" colspan="7">李春红,袁金兰,卢小娟,郭方杰,朱美</td>	</tr>	<tr>		<td class="ClassBlue" style="text-align:center">招标人定标原因及依据：</td>		<td class="ClassWhite" colspan="7">根据招标文件的评标、定标方法</td>	</tr>	<tr>		<td class="ClassBlue" style="text-align:center">中标结果公告发布日期：</td>		<td class="ClassWhite" colspan="7">2019年07月17日</td>	</tr>	</tbody></table>"""

    test_html="""<table id="_Sheet1" align="center" cellpadding="0" cellspacing="0" style="table-layout: fixed;font-family:宋体;font-size:9pt;color:#000000;border-collapse:collapse;" border="0" width="842">	<tbody><tr height="0px" style="font-size: 0px;line-height:0px;">		<td width="173px" style="border-left:#0000 1px solid;border-right:#0000  1px solid;">&nbsp;</td>		<td width="149px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="88px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="98px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="95px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="88px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="74px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="77px" style="border-right:#0000 1px solid;">&nbsp;</td>	</tr>	<tr>		<td style="border-bottom:#d1e6fa 1px solid;font-size:14pt;color:#ff0000;font-weight:bold;padding:2px;text-align:center" colspan="8">2019-2020年度镇江文旅集团部分小型建设项目镇江文旅集团2019年度招标代理服务框架招标的中标公告</td>	</tr>	<tr height="35px">		<td class="ClassBlue" style="text-align:center">项目编号:</td>		<td class="ClassWhite" colspan="7">ZJS2019061522</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">项目名称:</td>		<td class="ClassWhite" colspan="7">2019-2020年度镇江文旅集团部分小型建设项目</td>	</tr>	<tr height="35px">		<td class="ClassBlue" style="text-align:center">标段编号:</td>		<td class="ClassWhite" colspan="7">ZJS2019061522-02</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">标段名称:</td>		<td class="ClassWhite" colspan="7">镇江文旅集团2019年度招标代理服务框架招标</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">招标人名称:</td>		<td class="ClassWhite" colspan="7">镇江文化旅游产业集团有限责任公司</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">项目类型:</td>		<td class="ClassWhite" colspan="7">		</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">招标方式:</td>		<td class="ClassWhite" colspan="7">公开招标		</td>	</tr>	<tr height="53px">		<td class="ClassBlue" style="text-align:center"><br>序号</td>		<td class="ClassBlue" style="text-align:center">中标人名称</td>		<td class="ClassBlue" style="text-align:center">项目负责人姓名</td>		<td class="ClassBlue" style="text-align:center">项目负责人资质等级</td>		<td class="ClassBlue" style="text-align:center">项目负责人注册证号</td>		<td class="ClassBlue" style="text-align:center">中标价(元)</td>		<td class="ClassBlue" style="text-align:center">中标工期(日历天)</td>		<td class="ClassBlue" style="text-align:center">质量标准</td>	</tr>	<tr>		<td class="ClassWhite" style="text-align:center">1</td>		<td class="ClassWhite">镇江市华辰招标代理咨询有限公司</td>		<td class="ClassWhite">瞿志钢</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>	<tr>		<td class="ClassWhite" style="text-align:center">2</td>		<td class="ClassWhite">江苏大洲工程项目管理有限公司</td>		<td class="ClassWhite">王立冈</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>	<tr>		<td class="ClassWhite" style="text-align:center">3</td>		<td class="ClassWhite">江苏唯诚建设咨询有限公司</td>		<td class="ClassWhite">陈刚</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">定标时间：</td>		<td class="ClassWhite" colspan="7">&nbsp;</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">工程地点：</td>		<td class="ClassWhite" colspan="7">镇江市</td>	</tr>	<tr height="30px">		<td class="ClassBlue" style="text-align:center">评标委员会成员:</td>		<td class="ClassWhite" colspan="7">李春红,袁金兰,卢小娟,郭方杰,朱美</td>	</tr>	<tr>		<td class="ClassBlue" style="text-align:center">招标人定标原因及依据：</td>		<td class="ClassWhite" colspan="7">根据招标文件的评标、定标方法</td>	</tr>	<tr>		<td class="ClassBlue" style="text-align:center">中标结果公告发布日期：</td>		<td class="ClassWhite" colspan="7">2019年07月17日</td>	</tr>	</tbody></table>"""

    test_html="""<table id="_Sheet1_2_0" cellpadding="0" cellspacing="0" style="table-layout: fixed;font-family:SimSun;font-size:9pt;color:#000000;border-collapse:collapse;" border="0" width="1201">	<tbody><tr height="0px" style="font-size: 0px;line-height:0px;">		<td width="345px" style="border-left:#0000 1px solid;border-right:#0000  1px solid;">&nbsp;</td>		<td width="299px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="276px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="281px" style="border-right:#0000 1px solid;">&nbsp;</td>	</tr>	<tr height="24px">		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第一中标候选人</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第二中标候选人</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">第三中标候选人</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标候选人名称</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">南京平川工程项目管理有限公司</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">南京第一建设事务所有限责任公司</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">江苏大洲工程项目管理有限公司</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标报价(元)</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">443700.00</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人姓名</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">梅六宏</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">邵小刚</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">施成忠</td>	</tr>	<tr height="25px">		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">工期(天)</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">0</td>	</tr>	<tr height="25px">		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">质量要求</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人证书编号</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">32014170</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">32018806</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">32012201</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标人业绩</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>	</tr>	<tr>		<td width="345px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">项目负责人业绩</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>	</tr>	</tbody></table>"""

    test_html="""<table id="_Sheet1" align="center" cellpadding="0" cellspacing="0" style="table-layout: fixed;font-family:宋体;font-size:9pt;color:#000000;border-collapse:collapse;" border="0" width="842">	<tbody><tr height="53px">		<td class="ClassBlue" style="text-align:center"><br>序号</td>		<td class="ClassBlue" style="text-align:center">中标人名称</td>		<td class="ClassBlue" style="text-align:center">项目负责人姓名</td>		<td class="ClassBlue" style="text-align:center">项目负责人资质等级</td>		<td class="ClassBlue" style="text-align:center">项目负责人注册证号</td>		<td class="ClassBlue" style="text-align:center">中标价(元)</td>		<td class="ClassBlue" style="text-align:center">中标工期(日历天)</td>		<td class="ClassBlue" style="text-align:center">质量标准</td>	</tr>
<tr>		<td class="ClassWhite" style="text-align:center">1</td>		<td class="ClassWhite">镇江市华辰招标代理咨询有限公司</td>		<td class="ClassWhite">瞿志钢</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr><tr>		<td class="ClassWhite" style="text-align:center">2</td>		<td class="ClassWhite">江苏大洲工程项目管理有限公司</td>		<td class="ClassWhite">王立冈</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr><tr>		<td class="ClassWhite" style="text-align:center">3</td>		<td class="ClassWhite">江苏唯诚建设咨询有限公司</td>		<td class="ClassWhite">陈刚</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">&nbsp;</td>		<td class="ClassWhite">500000.00</td>		<td class="ClassWhite">365</td>		<td class="ClassWhite">合格		</td>	</tr>
</tbody></table>
"""
    test_html="""<table style="BORDER-TOP: medium none; BORDER-RIGHT: medium none; WIDTH: 437.75pt; BORDER-COLLAPSE: collapse; BORDER-BOTTOM: medium none; BORDER-LEFT: medium none" cellspacing="0" cellpadding="0" width="584" border="1">
  <tbody>
    <tr>
      <td style="BORDER-TOP: windowtext 1pt solid; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 62.1pt; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: windowtext 1pt solid; PADDING-RIGHT: 5.4pt" width="83">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph" align="center"><span>&nbsp;</span></p>
      </td>
      <td style="BORDER-TOP: windowtext 1pt solid; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 148.85pt; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: medium none; PADDING-RIGHT: 5.4pt" width="198">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 150%" align="center"><span style="FONT-FAMILY: 宋体; COLOR: black">招标人</span></p>
      </td>
      <td style="BORDER-TOP: windowtext 1pt solid; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 8cm; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: medium none; PADDING-RIGHT: 5.4pt" width="302">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 150%" align="center"><span style="FONT-FAMILY: 宋体; COLOR: black">招标代理单位</span></p>
      </td>
    </tr>
    <tr>
      <td style="BORDER-TOP: medium none; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 62.1pt; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: windowtext 1pt solid; PADDING-RIGHT: 5.4pt" width="83">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 150%" align="center"><span style="FONT-FAMILY: 宋体; COLOR: black">名</span><span style="COLOR: black">&nbsp; </span><span style="FONT-FAMILY: 宋体; COLOR: black">称</span></p>
      </td>
      <td style="BORDER-TOP: medium none; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 148.85pt; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: medium none; PADDING-RIGHT: 5.4pt" width="198">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 150%" align="center"><span style="FONT-FAMILY: 宋体; LINE-HEIGHT: 150%">常熟市恒翔建设有限公司、江苏中康建设有限公司</span></p>
      </td>
      <td style="BORDER-TOP: medium none; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 8cm; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: medium none; PADDING-RIGHT: 5.4pt" width="302">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 150%" align="center"><span style="FONT-FAMILY: 宋体; LINE-HEIGHT: 150%">建银工程咨询有限责任公司</span></p>
      </td>
    </tr>
    <tr>
      <td style="BORDER-TOP: medium none; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 62.1pt; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: windowtext 1pt solid; PADDING-RIGHT: 5.4pt" width="83">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 150%" align="center"><span style="FONT-FAMILY: 宋体; COLOR: black">联系人</span></p>
      </td>
      <td style="BORDER-TOP: medium none; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 148.85pt; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: medium none; PADDING-RIGHT: 5.4pt" valign="top" width="198">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph" align="center"><span style="FONT-FAMILY: 宋体">杨辰文、孙凌云</span></p>
      </td>
      <td style="BORDER-TOP: medium none; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 8cm; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: medium none; PADDING-RIGHT: 5.4pt" width="302">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 150%" align="center"><span style="FONT-FAMILY: 宋体; COLOR: black">殷梦超</span></p>
      </td>
    </tr>
    <tr>
      <td style="BORDER-TOP: medium none; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 62.1pt; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: windowtext 1pt solid; PADDING-RIGHT: 5.4pt" width="83">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 150%" align="center"><span style="FONT-FAMILY: 宋体; COLOR: black">联系电话</span></p>
      </td>
      <td style="BORDER-TOP: medium none; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 148.85pt; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: medium none; PADDING-RIGHT: 5.4pt" valign="top" width="198">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph" align="center"><span>0512-52985307</span><span style="FONT-FAMILY: 宋体">、</span><span>13962688272</span></p>
      </td>
      <td style="BORDER-TOP: medium none; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 8cm; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: medium none; PADDING-RIGHT: 5.4pt" width="302">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 150%" align="center"><span style="COLOR: black">0512-52891853</span></p>
      </td>
    </tr>
    <tr>
      <td style="BORDER-TOP: medium none; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 62.1pt; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: windowtext 1pt solid; PADDING-RIGHT: 5.4pt" width="83">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 150%" align="center"><span style="FONT-FAMILY: 宋体; COLOR: black">联系地址</span></p>
      </td>
      <td style="BORDER-TOP: medium none; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 148.85pt; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: medium none; PADDING-RIGHT: 5.4pt" width="198">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 150%" align="center"><span style="FONT-FAMILY: 宋体; LINE-HEIGHT: 150%">常熟市渠中路藕渠家园五楼、昆山开发区郁金香路</span><span style="LINE-HEIGHT: 150%">499</span><span style="FONT-FAMILY: 宋体; LINE-HEIGHT: 150%">号</span><span style="LINE-HEIGHT: 150%">B</span><span style="FONT-FAMILY: 宋体; LINE-HEIGHT: 150%">栋</span><span style="LINE-HEIGHT: 150%">4-5</span><span style="FONT-FAMILY: 宋体; LINE-HEIGHT: 150%">层</span></p>
      </td>
      <td style="BORDER-TOP: medium none; BORDER-RIGHT: windowtext 1pt solid; WIDTH: 8cm; BORDER-BOTTOM: windowtext 1pt solid; PADDING-BOTTOM: 0cm; PADDING-TOP: 0cm; PADDING-LEFT: 5.4pt; BORDER-LEFT: medium none; PADDING-RIGHT: 5.4pt" width="302">
      <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman','serif'; TEXT-ALIGN: center; MARGIN: 0cm 0cm 0pt; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 150%" align="center"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; LINE-HEIGHT: 150%">常熟市长江路</span><span style="FONT-SIZE: 12pt; LINE-HEIGHT: 150%">134</span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; LINE-HEIGHT: 150%">号</span></p>
      </td>
    </tr>
  </tbody>
</table>"""
    sel = Selector(text=test_html)
    pprint(common_table_extrator(sel))