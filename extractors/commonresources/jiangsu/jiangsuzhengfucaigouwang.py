# -*- coding: UTF-8 -*-
"""
@author:wubailong
@time:2020/11/23
江苏政府采购网
search_dict = {
    "source_type": "江苏政府采购网",
    #"公告类型": "建设工程 ",
    #"工程类型": "中标结果公告",
    "city": "南京",  # # 省级/南京市/无锡市/徐州市/常州市/苏州市/南通市/连云港市/淮安市/盐城市/扬州市/镇江市/泰州市/宿迁市/
}
# 文件名配置
cfgs = {
    "your_name": "QuinceyWu",
    "source_type": "jszfcg",
    "type": "zb",
}
"""
import os
from extractors.base_extractor import BaseExtractor
from spidertools.utils.xpath_utils import get_alltext, get_all_tables
from spidertools.utils.text_utils import replace_punctuation
from spidertools.utils.snippets import combine_two_dict
from info_fsm import InfoMachine
from table_info_extract.common_table_utils import common_table_extrator
from table_info_extract import dict_mapping_triedTree
from pprint import pprint


class JiangSuZhengFuCaiGouWang(BaseExtractor):
    def node(self):
        pass

    def commom_announcement_parse(self):
        #print(self.html.count("</p>"))
        #self.html = self.html.replace("""<span style="font-size:14.0pt;font-family:仿宋;mso-font-kerning:0pt">名称：</span>""", "")
        if self.html.count("</p>") <= 3:
            # 获取招标公告正文
            content_root_nodes = self.sel.xpath("//div[@class='detail_con']")
        else:
            content_root_nodes = self.sel.xpath("//p")
        texts = []

        # 遍历所有子节点，获取相应的文本
        for node in content_root_nodes:
            node_text = get_alltext(node)
            node_text = node_text.replace(" ", "")
            texts.append(node_text)

        clean_texts = []
        # 清理文本中的一些空几个，不可见字符，以及加载关键字中间的空格
        for text in texts:
            text = replace_punctuation(text.strip())
            clean_texts.append(text)

        # 创建状态机
        machine = InfoMachine(self.base_pattern)
        # 执行状态机，解析整个文本
        output_dict = machine.run_list(clean_texts)

        # 获取所有的table表格
        tables = get_all_tables(self.sel)
        for table in tables:
            # print(table)
            result = common_table_extrator(table)
            output_dict = combine_two_dict(output_dict, result)
        html_info_dict = dict_mapping_triedTree(self.info_dict)
        output_dict = combine_two_dict(output_dict, html_info_dict)

        if '工程基本信息' not in output_dict.keys():
            output_dict['工程基本信息'] = {}
        output_dict['工程基本信息']['项目名称'] = output_dict['工程公告信息']['公告标题']

        if '工程招标信息' not in output_dict.keys():
            output_dict['工程招标信息'] = {}
        output_dict['工程招标信息']['标段名称'] = output_dict['工程公告信息']['公告标题']
        return output_dict

    def start_parse(self):
        result = self.commom_announcement_parse()
        html_info_dict = dict_mapping_triedTree(self.info_dict)
        result = combine_two_dict(result, html_info_dict)
        return result


if __name__ == '__main__':
    info_dict = {}
    for root, dirs, files, in os.walk('../../../demo_html/demo_wbl'):
        for i, name in enumerate(files):
            if "init" not in name:
                print(f"\033[32m{i + 1}=============={name}\033[0m")
                with open(f'../../../demo_html/demo_wbl/{name}', 'r', encoding='utf-8') as fr:
                    html = fr.read()
                info_dict['html'] = html
                info_dict['公告类型'] = "公开招标公告"  # "中标结果公告""公开招标公告""邀请招标公告"
                obj = JiangSuZhengFuCaiGouWang(info_dict)
                result = obj.start_parse()
                pprint(result)
