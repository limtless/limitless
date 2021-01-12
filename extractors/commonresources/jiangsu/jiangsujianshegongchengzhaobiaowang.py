# -*- coding: utf-8 -*-
from scrapy.selector import Selector
from spidertools.utils.xpath_utils import get_alltext,get_all_tables
from spidertools.utils.text_utils import replace_punctuation
from spidertools.utils.snippets import combine_two_dict
from info_fsm import InfoMachine
from pprint import pprint
import re
import os
from table_info_extract.extract_utils import table_info_extract_styletwo,table_info_extract_stylethree
from table_info_extract import dict_mapping_triedTree
from table_info_extract.common_table_utils import common_table_extrator
from extractors.base_extractor import BaseExtractor

class JiangSuJianSheGongChengZhaoBiaoWang(BaseExtractor):
    def __init__(self,info_dict):
        super(JiangSuJianSheGongChengZhaoBiaoWang, self).__init__(info_dict)
        self.build =0

    def parse_bid_evaluation_results_announcement(self):
        '''
        评标结果公告提取
        :return:
        '''
        body_text = get_alltext(self.sel.xpath('//body'))
        machine = InfoMachine(self.base_pattern)
        clean_text  = replace_punctuation(body_text.strip())

        output = machine.run_list([clean_text])
        #output_dict = combine_two_dict(output, self.info_dict)

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
            output_dict = combine_two_dict(output_dict,result)


        return output_dict

    def commom_announcement_parse(self):
        '''
        通用网页公告解析
        :return:
        '''

        # 获取招标公告正文
        content_root_nodes = self.sel.xpath('//body')#调用了之前设置的selector对象
        texts = []

        # 遍历所有子节点，获取相应的文本
        for node in content_root_nodes:
            node_text = get_alltext(node)
            texts.append(node_text)

        clean_texts = []
        # 清理文本中的一些空几个，不可见字符，以及加载关键字中间的空格
        for text in texts:
            text = replace_punctuation(text.strip())#strip用于去除首尾空格,replace_punctuation去除各种符号
            clean_texts.append(text)

        # 创建状态机
        machine = InfoMachine(self.base_pattern)#调用了info_fsm.py的InfoMachine,base_pattern = '%s:\s*(.*)'
        # 执行状态机，解析整个文本
        output_dict = machine.run_list(clean_texts)#调用实例化后的run_list方法



        #获取所有的table表格
        tables = get_all_tables(self.sel)#该方法与get_alltext一样来自于spidertools工具中
        for table in tables:
            result = common_table_extrator(table)#调用通用表格转换模板
            output_dict = combine_two_dict(output_dict, result)

        return output_dict


    def parse_win_bidding_announcement(self):
        '''
        中标公告信息提取
        :return:
        '''

        table_node = self.sel.xpath('//table[@id="Table1"]')
        output_dict = common_table_extrator(table_node)
        return output_dict


    def parse_bid_announcemen(self):
        '''
        招标信息提取
        :param root:
        :return:
        '''



        output_dict = {}

        # aaa = self.html.split('特殊公告',1)[0]#截断网页
        self.html = """<table id="_Sheet1" align="center" cellpadding="0" cellspacing="0" style="table-layout: fixed;font-family:SimSun;font-size:9pt;color:#000000;border-collapse:collapse;" border="0" width="871">	<tbody><tr height="0px" style="font-size: 0px;line-height:0px;">		<td width="50px" style="border-left:#0000 0px solid;border-right:#0000  1px solid;">&nbsp;</td>		<td width="115px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="41px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="75px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="118px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="22px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="123px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="75px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="132px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="122px" style="border-right:#0000 0px solid;">&nbsp;</td>	</tr>	<tr height="38px">		<td style="font-family:SimHei;font-size:18pt;padding:2px;text-align:center" colspan="10">常州市建设工程招标公告</td>	</tr>	<tr height="40px">		<td style="text-align:left;font-size:14pt;font-weight:bold;padding:2px;">一、</td>		<td style="text-align:left;font-size:14pt;font-weight:bold;padding:2px;">招标条件	</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>	</tr>	<tr>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:10.5pt;padding:2px;" colspan="9">	<p style="LINE-HEIGHT:25px"><span style="font-size:12pt;">&nbsp;&nbsp;</span><span style="font-size:12pt;font-weight:bold;">&nbsp;</span><span style="font-size:12pt;">&nbsp;</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">空港八村保障性安居工程项目场外配套工程</span><span style="font-size:12pt;">&nbsp;</span><span style="font-size:12pt;">已由</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">常州国家高新技术产业开发区（新北区）行政审批局</span><span style="font-size:12pt;">以</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">批文名为：关于空港八村保障性安居工程项目核准的批复&nbsp;编号为：常新行审经计[2017]10号</span><span style="font-size:12pt;">批准建设，招标人为</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">常州新航智造园建设管理有限公司</span><span style="font-size:12pt;">，建设资金来自</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">自筹</span><span style="font-size:12pt;">，项目出资比例为</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">国有资金：100.00&nbsp;%,私有资金：0.00&nbsp;%,外国政府及组织投资:0.00&nbsp;%,境外私人投资:0.00&nbsp;%</span><span style="font-size:12pt;">。项目已具备招标条件，现对该项目的施工进行公开招标。</span>&nbsp;	</p>		</td>	</tr>	<tr height="40px">		<td style="text-align:left;font-size:14pt;font-weight:bold;padding:2px;">二、</td>		<td style="text-align:left;font-size:14pt;font-weight:bold;padding:2px;">项目概况</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>	</tr>	<tr height="30px">		<td style="text-align:left;padding:2px;">	<p>&nbsp;	</p>		</td>		<td style="text-align:left;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">工程地点：</span><span style="font-size:10.5pt;">&nbsp;&nbsp;</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">常州市新北区罗溪镇</span>	</p>		</td>	</tr>	<tr>		<td style="text-align:left;padding:2px;">		</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">工程规模：</span><span style="font-size:12pt;">&nbsp;</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">243055平方米</span>	</p>		</td>	</tr>	<tr>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">质量等级要求：</span><span style="font-size:12pt;">&nbsp;</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">合格</span>	</p>		</td>	</tr>	<tr height="30px">		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">计划开竣工时间：</span><span style="font-size:12pt;">&nbsp;</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">2019年11月01日</span><span style="font-size:12pt;">至</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">2020年03月29日</span>	</p>		</td>	</tr>	<tr>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="8">	<p style="LINE-HEIGHT:25px"><span style="font-size:12pt;">投资总额：</span><span style="font-size:12pt;">&nbsp;&nbsp;</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">109161.00&nbsp;万元</span>&nbsp;	</p>		</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>	</tr>	<tr>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">结构类型：</span><span style="font-size:12pt;">&nbsp;</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">其他&nbsp;</span><span style="font-size:12pt;">&nbsp;</span>&nbsp;	</p>		</td>	</tr>	<tr>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">本次招标范围：</span><span style="font-size:12pt;">&nbsp;</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">园林绿化工程;道路及地下管线工程;其他;土石方工程;</span>	</p>		</td>	</tr>	<tr height="25px">		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>	</tr>	<tr height="25px">		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>	</tr>	<tr height="40px">		<td style="text-align:left;font-size:14pt;font-weight:bold;padding:2px;">三、</td>		<td style="text-align:left;font-size:14pt;font-weight:bold;padding:2px;" colspan="2">投标人资格条件</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>	</tr>	<tr height="30px">		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">本招标工程共分</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">1</span><span style="font-size:12pt;">个标段，标段划分及投标人资格要求如下：</span>&nbsp;	</p>		</td>	</tr>	<tr>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="9"><a name="子网格"></a>	<table id="_Sheet1_15_1" cellpadding="0" cellspacing="0" style="table-layout: fixed;font-family:SimSun;font-size:9pt;color:#000000;border-collapse:collapse;" border="0" width="819">	<tbody><tr height="0px" style="font-size: 0px;line-height:0px;">		<td width="140px" style="border-left:#0000 1px solid;border-right:#0000  1px solid;">&nbsp;</td>		<td width="178px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="112px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="164px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="103px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td width="122px" style="border-right:#0000 1px solid;">&nbsp;</td>	</tr>	<tr height="39px">		<td width="140px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">标段序号</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">标段内容</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">标段面积<br>(平方米)</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">估算价（万元）</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">投标人资质类别、等级</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">注册建造师专业、等级</td>	</tr>	<tr>		<td width="140px" style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">3204111705230103-BD-004</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">园林绿化工程;道路及地下管线工程;其他;土石方工程</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">&nbsp;</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;overflow:hidden;white-space:nowrap;text-overflow:clip;width:163px;font-size:12pt;padding:2px;text-align:center">1550.00</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">[市政公用工程三级](含)以上</td>		<td style="border-left:#000000 1px solid;border-right:#000000 1px solid;border-top:#000000 1px solid;border-bottom:#000000 1px solid;font-size:12pt;padding:2px;text-align:center">[市政公用工程二级](含)以上</td>	</tr>	</tbody></table>		</td>	</tr>	<tr height="2px">		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>	</tr>	<tr>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;" colspan="9">	<p>&nbsp;	</p>		</td>	</tr>	<tr>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">3.1&nbsp;本次招标</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">不接受</span><span style="font-size:12pt;">联合体投标。联合体投标的，应满足下列要求：</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">&nbsp;</span>	</p>		</td>	</tr>	<tr>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">3.2&nbsp;报名其他条件</span>&nbsp;&nbsp;<span style="font-size:12pt;font-weight:bold;text-decoration:underline;">&nbsp;</span>	</p>		</td>	</tr>	<tr height="40px">		<td style="text-align:left;font-size:14pt;font-weight:bold;padding:2px;">四、</td>		<td style="text-align:left;font-size:14pt;font-weight:bold;padding:2px;" colspan="2">招标文件的获取</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>	</tr>	<tr>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">凡有意参加投标者，可于</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">2019年10月12日</span><span style="font-size:12pt;">至</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">2019年10月16日</span><span style="font-size:12pt;">登陆&nbsp;“常州市工程交易网”“投标单位登录”栏目获取本项目招标文件。</span>&nbsp;	</p>		</td>	</tr>	<tr height="30px">		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">招标文件每套售价</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">300.00</span><span style="font-size:12pt;">元，售后不退。</span>&nbsp;	</p>		</td>	</tr>	<tr height="40px">		<td style="text-align:left;font-size:14pt;font-weight:bold;padding:2px;">五、</td>		<td style="text-align:left;font-size:14pt;font-weight:bold;padding:2px;" colspan="2">公告发布</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>	</tr>	<tr height="30px">		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">本公告发布媒体为：</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">江苏省建设工程招标网、常州市工程交易网</span>	</p>		</td>	</tr>	<tr height="30px">		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">本公告发布时间为：</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">2019年10月12日</span><span style="font-size:12pt;">至</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">2019年10月16日</span>	</p>		</td>	</tr>	<tr height="30px">		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">本项目资格审查办法：</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">见附件</span>&nbsp;	</p>		</td>	</tr>	<tr height="30px">		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;" colspan="9">	<p><span style="font-size:12pt;">本项目评标细则：</span><span style="font-size:12pt;font-weight:bold;text-decoration:underline;">见附件</span>&nbsp;	</p>		</td>	</tr>	<tr height="40px">		<td style="text-align:left;font-size:14pt;font-weight:bold;padding:2px;">六、</td>		<td style="text-align:left;font-size:14pt;font-weight:bold;padding:2px;">联系方式</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>	</tr>	<tr>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">招&nbsp;标&nbsp;人：</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="4">常州新航智造园建设管理有限公司</td>		<td style="text-align:left;font-size:12pt;padding:2px;">招标代理机构：</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="3">常州中瑞工程造价咨询有限公司</td>	</tr>	<tr>		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">地&nbsp;址：</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="4">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">地&nbsp;址：</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="3">常州市新北区友邦商务大厦1幢1301室-13066室、1308室、1105室</td>	</tr>	<tr height="25px">		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">邮&nbsp;编：</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="4">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">邮&nbsp;编：</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="3">&nbsp;</td>	</tr>	<tr height="25px">		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">联&nbsp;系&nbsp;人：</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="4">王亚明</td>		<td style="text-align:left;font-size:12pt;padding:2px;">项目组组长：</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="3">宣志鹏</td>	</tr>	<tr height="25px">		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">电&nbsp;话：</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="4">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">电&nbsp;话：		</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="3">0519-85606263</td>	</tr>	<tr height="25px">		<td style="text-align:left;font-size:12pt;padding:2px;">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">传&nbsp;真：</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="4">&nbsp;</td>		<td style="text-align:left;font-size:12pt;padding:2px;">传&nbsp;真：</td>		<td style="text-align:left;font-size:12pt;padding:2px;" colspan="3">0519-85603579</td>	</tr>	<tr height="25px">		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>		<td style="text-align:left;padding:2px;">&nbsp;</td>	</tr>	<tr>		<td style="text-align:left;padding:2px;" colspan="10">	<p><span style="font-size:12pt;color:#ff0000;">注1：如果您是第一次来常州地区参加电子化投标，请您携带好本企业的相关资料先办理企业信息登记手续。如在投标（报名）截止时间前未进行企业信息登记,可能导致无法进场交易。请按照常州市工程交易网</span><a href="#" onclick="window.open('http://www.czgcjy.com/czztb/bszn/')"><font size="4">“办事指南”</font></a>		<span style="font-size:12pt;color:#ff0000;">栏目中的</span><a href="#" onclick="window.open('http://www.czgcjy.com/czztb/InfoDetail/?InfoID=a842b97a-5a27-442d-b283-8a238157a2b4&amp;CategoryNum=008')"><font size="4">“常州市诚信数据库操作手册”</font></a>		<span style="font-size:12pt;color:#ff0000;">要求办理。	</span>&nbsp;	</p>		</td>	</tr>	<tr>		<td style="text-align:left;font-size:12pt;color:#ff0000;padding:2px;" colspan="10">注2：投标人可在本招标公告页尾的信息发布栏内查阅本次招投标的“公告发布、招标文件、招标文件答疑澄清、招标控制价发布及答疑澄清”等全部相关信息，因未能及时了解相关最新信息所引起的投标失误责任自负。&nbsp;</td>	</tr>	</tbody></table>"""
        # self.sel = Selector(text=self.html)



        # 获取所有的table表格
        tables = get_all_tables(self.sel)
        for table in tables:
            result = common_table_extrator(table)
            print("---")
            print(result)
            output_dict = combine_two_dict(output_dict, result)
        info_dict = output_dict

        #将结构化数据转化为table相关层次结构
        #info_dict = dict_mapping_triedTree(result)

        #获取招标公告正文
        content_root_nodes = self.sel.xpath('//tr[@id="trzygg"]')
        # content_root_nodes = self.sel.xpath('//p')  #待验证能否用P标签
        if content_root_nodes:
            texts = []

            # 遍历所有子节点，获取相应的文本
            for node in content_root_nodes:
                node_text = get_alltext(node)
                if '（投）' or '(投)'in node_text:
                    node_text =node_text.replace('（投）','投')
                    node_text = node_text.replace('(投)', '投')
                if "投标报名联系人及联系方式" in node_text:
                    if "投标报名联系人及联系方式：" in node_text:
                        node_text=node_text.replace('投标报名联系人及联系方式：','投标报名联系人及联系方式:')#特殊处理，为匹配招标信息
                    elif "投标报名联系人及联系方式:" in node_text:
                        pass
                    elif "投标报名联系人及联系方式：" not in node_text and "投标报名联系人及联系方式:" not in node_text:
                        node_text = node_text.replace('投标报名联系人及联系方式', '投标报名联系人及联系方式:')
                else:
                    pass
                texts.append(node_text)

            #创建状态机
            machine = InfoMachine(self.base_pattern)
            clean_texts = []
            # 清理文本中的一些空几个，不可见字符，以及加载关键字中间的空格
            for text in texts:
                text = replace_punctuation(text.strip())
                text = text.replace('\xa0','')
                text = text.replace('\t', '')
                text = text.replace('\u3000', '')
                clean_texts.append(text)
            #执行状态机，解析整个文本
            print("clean_texts:",clean_texts)
            output = machine.run_list(clean_texts)
            output_dict = combine_two_dict(output, info_dict)

        #获取其他的表格信息
        child_nodes = self.sel.xpath('//tr[@id="trzygg"]//span[@id="zygg_kkk"]/*')
        if child_nodes:
            check_has_meta = False
            for child in child_nodes:
                if child.root.tag == 'meta' or child.root.tag == "epointform":
                    check_has_meta = True
                    break
            if check_has_meta:
                taget_table = self.sel.xpath('//tr[@id="trzygg"]//span[@id="zygg_kkk"]//table//table')
            else:
                taget_table = self.sel.xpath('//tr[@id="trzygg"]//span[@id="zygg_kkk"]//table')
            table_info_dict = table_info_extract_stylethree(taget_table)
            table_convert_dict = dict_mapping_triedTree(table_info_dict)
            output_dict = combine_two_dict(output_dict,table_convert_dict)


        output_dict = clean_dict(output_dict)  # 消除多余字符并且去重
        return output_dict



    def start_parse(self):
        result = {}
        if '招标公告' in self.info_dict['公告类型']:
            result = self.parse_bid_announcemen()
        elif '中标结果公告' in self.info_dict['公告类型']:
            result = self.parse_win_bidding_announcement()
        elif '未入围公示' in self.info_dict['公告类型']:
            pass
            #result = self.parse_not_shortlisted_announcement()
        elif '评标结果公示' in self.info_dict['公告类型']:
            pass
            #result = self.parse_bid_evaluation_results_announcement()

        return result



    def get_line_like_nodes(self,roots):
        node_list = []


        sub_nodes = roots.xpath('./*')
        for sub_node in sub_nodes:
            if sub_node.attrib and ('id' in sub_node.attrib):
                id  = sub_node.attrib['id']
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

def clean_dict(output_dict):   #提供更干净的输出内容
    try:
        for x in output_dict["工程基本信息"].keys():
            if type(output_dict["工程基本信息"][x])==str:
                output_dict["工程基本信息"][x] = output_dict["工程基本信息"][x].replace(' ', '')
                output_dict["工程基本信息"][x] = output_dict["工程基本信息"][x].replace('\xa0', '')
                output_dict["工程基本信息"][x] = output_dict["工程基本信息"][x].replace('\t', '')
            else:
                pass
        for i in output_dict["工程招标信息"].keys():
            if type(output_dict["工程招标信息"][i]) == list:
                new_list =[]
                for a in output_dict["工程招标信息"][i]:
                    a = a.replace(' ', '')
                    a = a.replace('\xa0', '')
                    a = a.replace('\t', '')
                    new_list.append(a)
                output_dict["工程招标信息"][i] = new_list#消除多余字符
                output_dict["工程招标信息"][i] = list(set(output_dict["工程招标信息"][i]))#去重
            else:
                output_dict["工程招标信息"][i] = output_dict["工程招标信息"][i].replace('\xa0', '')
                output_dict["工程招标信息"][i] = output_dict["工程招标信息"][i].replace('\t', '')
                pass
        if output_dict['未知']['未知邮编']==['E－mail']:
            del output_dict['未知']['未知邮编']
        return output_dict
    except Exception as o:
        try:
            if output_dict['未知']['未知邮编']==['E－mail']:
                del output_dict['未知']['未知邮编']
        except Exception as n:
            pass
        return output_dict




if __name__ == '__main__':
    info_dict = {}
    path ='../../../demo_html/1.9'
    for root, dirs, files, in os.walk(path):
        for i,name in enumerate(files):
            if "init" not in name:
                print(f"\033[32m{i+1}=============={name}\033[0m")
                # with open(f'../../../demo_html/zhaobiao/{name}', 'r', encoding='utf-8') as fr:
                with open(f'{path}'+'/'+f'{name}', 'r', encoding='utf-8') as fr:
                    html = fr.read()
                info_dict['html'] = html
                info_dict['公告类型'] = "招标公告"  # "中标结果公告"
                obj = JiangSuJianSheGongChengZhaoBiaoWang(info_dict)
                result = obj.start_parse()
                pprint(result)



if __name__ == '__main__':
    import requests
    zhaobiao_url = "http://www.jszb.com.cn/jszb/YW_info/ZhaoBiaoGG/ViewReportDetail.aspx?RowID=692652&categoryNum=012&siteid=1"
    zhongbiao_url = "http://www.jszb.com.cn/JSZB/yw_info/ZhongBiaoGS/ViewGSDetail.aspx?RowID=1297866&siteid=1&categoryNum=7"
    not_in_url = "http://www.jszb.com.cn/JSZB/yw_info/ZiGeYS/ViewYSDetail.aspx?RowID=158068&siteid=1&categoryNum=8"
    bid_evaulate_url = "http://www.jszb.com.cn/JSZB/yw_info/HouXuanRenGS/ViewHXRDetail.aspx?GongGaoGuid=ec62fb01-6c99-4863-aecc-6eb081380a30"

    req = requests.get(zhaobiao_url)#通过修改网址，得到不同的结果
    info_dict = {}
    info_dict['_id'] = "_id"
    info_dict['html'] = req.text
    info_dict['公告类型'] = "招标公告"
    obj = JiangSuJianSheGongChengZhaoBiaoWang(info_dict)#把信息传给类
    result = obj.parse_bid_announcemen()#解析
    pprint(result)