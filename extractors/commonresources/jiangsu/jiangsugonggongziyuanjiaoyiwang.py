from pprint import pprint

from lxml import etree
from spidertools.utils.xpath_utils import get_alltext, get_all_tables
from spidertools.utils.text_utils import replace_punctuation
from spidertools.utils.snippets import combine_two_dict

from scrapy.selector import Selector
from configs.commom import FlagUtil
from configs.logging_settings import LogStateString
from extractors.base_extractor import BaseExtractor
from info_fsm import InfoMachine
import re

from table_info_extract import dict_mapping_triedTree

from table_info_extract.common_table_utils import common_table_extrator
from utils.logger_utils import savelog


class JiangSuGongGongZiYuanJiaoYiWang(BaseExtractor):
    def __init__(self, info_dict):
        self.dict_repl_danwei = {
            r'中标总价（元）/费率为': "中标总价",
            r'中标总价（元）/费率': "中标总价",
            r'中标工期\(日历天\)': "中标工期",
            r'中标总价（元）': '中标总价',
            r'中标价\(元\)': "中标价",
            r'中标金额（元/费率）': "中标金额",
            r'中标工期（天/月）': "中标工期",
            r'（万元）': "",
            r'万元': "",
            r'\(万元\)': "",
            r'（%）': "",
            r"合同估算价": "招标估算价",
        }
        info_dict = self.repl_danwei(info_dict)
        super(JiangSuGongGongZiYuanJiaoYiWang, self).__init__(info_dict)
        self.dict_repls = {
            r'\?:': ":",
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20200423/2b897ef6-a940-4131-9570-d9d546d75af9.html
            # 注：双引号未被替换为英文的
            # common
            r'信息发布时间:': '',
            r"投标报价:.{1,40}分": "",
            r"标文件制作工具使用说明": "\n标文件制作工具使用说明",
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20200326/0f1e0fbe-14a9-47d6-8e04-ce0580f542a1.html
            r"按《铁路基本建设工程设计概": "\n按《铁路基本建设工程设计概",
            r"工程监理:工程施工图设计阶段": "",
            r'报价:满?分?\d*分': "\n",
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190806/cfbc508c-9b44-4989-ae3e-ee0a9492173f.html
            r'投标报价:以有效投标': "\n\n",
            r"电话.{1,4}\d*.{1,4}开具收据": "",
            r"在投标截止前": "\n在投标截止前",
            r'投标报价:以?当?有效': "",  # 投标报价：以有效投标文件的评标价进行算术平均
            r'开户银行': "\n开户银行",
            r"密码锁激活:": "\n密码锁激活:",
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20191206/403eb164-689d-4005-bec4-434e9005dd87.html
            r'逾期送达的投标文件': '\n逾期送达的投标文件',
            # 无锡市=======
            r"招 ?标 ?人\(公章及法.*?章\)": "招标人:",  # 适配：公章及法人签章 公章及法人章 公章及法定代表人签章
            r"招标代理机构\(公章及法.*?章\)": "招标代理机构:",  # 公章及法人签章 公章及法人章 公章及法定代表人签章
            r'所有投标人登录江阴市建设工程网上招投标系统V7.0\(网址': '',
            r'建设工程网上招投标系统V7.0诚信信息库入库指南\(网址': '',
            r'获取招标文件、清单、图纸\(网址': '',
            r'施工项目经理:具有一级注册建造师': '',  # 待商议，12.18商议结果可以替换掉
            r'项目负责人要求:配备一名': '',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190108/622eb15c-a4eb-4085-9375-2618897527d6.html
            r'地点为网上投标网址': '',
            r'项目负责人:国家注册壹级建造师': '',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190123/89420bf5-4a4b-4d0a-b322-1dddbee98849.html
            r'分中心开标室1.{0,2}\(地址': '',
            r'无锡市公共资源交易中心新吴分中心\(地址': '',
            r'投标人拟派项目负责人': '',  # 拟派项目负责人须具备以下条件
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190827/168e9c06-1e9d-4074-af81-ff920b1e3429.html
            r'项目负责人:1\)具有省级及以上有关主管部门颁发的': '',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190505/a02a8ee5-ba3a-4ad9-a99b-1c143db59eaa.html
            r'负责人:1\)年龄55周岁及以下': '',
            r'工程建安费约2500万元': "拟派项目负责人须具备以下条件:",  # 额外空v的添加关键字，触发mode，需要带冒号
            # 徐州市=======
            r'及时联系技术支持客服电话, ?电话为:': '',
            # 可以有空格  http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20201204/7c3f829e-be7a-4184-8699-ed86f86657d8.html
            r'请及时联系技术支持客服电话:': '',
            r'房间\(电话:': "",
            r'如不明确,请拨打.*?电话:': '',  # 兼容：如不明确,请拨打电话  //如不明确，请拨打9号窗口电话
            # r'徐州”\[网址:': '',  # 诚信徐州”[网址//信用徐州”[网址 # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190929/e8f1e468-785e-4c0b-8473-db96f186c90b.html
            # r'源交易中心”\[网址:': '',
            # r'政府”[网址:':"",
            # """情况太多了，用下面的代替"""
            r'”\[ ?网 ?址 ?: ?': '',
            # 都可以有空格 http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20200929/9514162b-d919-4a54-824e-5da546b8fb33.html
            r'电话:0516-67012705': '',
            # 招投标监督管理部门及电话 http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190929/4eeb114c-72b7-472e-b049-71e422825652.html

            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20200807/68aaf94a-337b-441b-bd0f-2342af36b541.html
            r'账户名称:.*?中心': "",  # 账户名称：徐州市铜山区工程建设服务中心
            r'账户名称:徐州市.*?': '',
            r'批文名称:': '',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20181012/c2001312-59ab-4024-8177-318c707e6246.html
            r'名称:睢宁县公共资源交易中心': '',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20201105/0c0c994f-5350-41b9-bed7-7ea35b4efc0d.html
            # 已确定是无用信息 # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20200527/8648a4b0-a981-4e12-bc10-adb8013c2b37.html
            r'合同估算价': '拟派项目负责人须具备以下条件: 合同估算价',
            # 以下是针对于两个标段的特殊处理，将两个标段合并为一个，进行存储
            r'；二标段名称:': '二',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190929/d3639504-7fc1-44e2-990b-7fad5dfb6c9f.html
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190929/81247272-c900-433e-b446-80862612696e.html
            # 镇江市
            r'服务中心A楼,地址:': '',
            r'备案手续\(联系电话:': "",
            r'号\(公共资源交易中心财务联系电话:': "",  # 兼容虚拟子帐号/虚拟子账号
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20181216/1ef39e2d-7127-4a75-a148-98e6e198a361.html
            r'其他': "\n其他",
            r'开标室\(\d*\)\(地址:': '',
            r'镇江水利交易系统\(网址': "",
            r'资源交易中心联系电话:': "",
            r'第一开标室,\(地址': "",
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20200417/d4bc8310-aa6e-4096-ba68-27b6271cfdaa.html
            r'不见面交易系统地址:': "",
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20200928/a3c5fad3-f89f-4950-b76d-c981bc35f56e.html
            r'公共服务平台。网址:': "",
            # 苏州市
            r'设计周期': "招标工期",
            r'招标代理机构联系方式': "招标代理机构联系方式:",
            r'个标段': "个标段\n",
            r'备注:': "\n备注:",
            r'网址:': "",  # 用不着，融合阶段也会舍弃
            # 盐城市
            r'文件正文PDF附件': "\n文件正文PDF附件",
            r'有下列情形之一的': "有下列情形之一的\n",
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190928/GG_67dfbccd-a7c2-4176-ad37-964592accede.html
            r'名称:睢宁县公共资源': "",
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20200720/016ac6ed-8888-4985-b5c1-f72ac3932569.html
            r'南京市公共资源交易中心1219室\(地址:': "",
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20200408/85fc5447-8902-445b-ae78-6e37c4c337b4.html
            r'单位地址:南京市建邺区奥体大街': "",
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20191118/7a780d19-9026-4053-bd46-145c82bfc301.html
            r'中心北门指定区域\(地址：南京市': "",
            r'电子签章\(联系人:': "",
            r'联系电话:0523-86893080': "联系电话:\n0523-86893080",
            r"\(公章\)": ":",
            r"\(盖?章\)": ":",  # 兼容(盖章)(章)

            r"收款单位\(地址": "",
            # 连云港
            r'地址:连云港': "",
            r'技术问题,电话:': "",
            r'指定区域\(地址:南京市': "",
            r'\d*室\(地址:': "",
            r'项目经理:须携带本人有效身份证原': "",
            r'::': ":"
        }
        self.list_obj_strs = [  # 前面优先级高
            '工程',
            '项目',
            '中心',
            '中转站',
            '雅居二期',
            '装备基地',
            '二标段',
            '档案馆',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20190927/cb2f1b05-3f4e-4257-a14c-575c24bdfec1.html
            '总部大楼',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190830/2feaf11d-ef88-4b85-924f-68877d1a2959.html
            '保障房三期',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191010/d419de09-eb0c-4d3c-be9a-c74c9cd0304c.html'
            '（北区）',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191015/c96a7f3e-f0d5-47b0-afea-fb1e3b746492.html
            '创意街区',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191015/7d7f4318-3fb6-4daa-ae2d-7e77f054b89c.html'
            '进行加固',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191016/24fe5192-4a8b-4286-912b-7f064a166551.html
            '贯制学校',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191016/316309d8-a236-4e8f-a54a-1b9ab2b5bd2f.html'
            '综合体',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191018/8d4a1df8-3c3f-4f0e-844e-aeffbeeb0a2a.html'
            '业务用房',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191024/f1b6757b-2124-41eb-bd3c-eda3c662d8e0.html'
            '地块（NO.2018G48）',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191024/98f14759-b6cb-40c5-bc1f-01850af81761.html'
            '用房土建',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191024/cc396a51-43e6-440b-a45d-1fa36d371703.html'
            '眼科医院',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191029/bd82a6e5-d73a-4a3f-b3c2-098302978879.html'
            '虚拟产业园',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191029/c8c03a5f-03f9-4705-a8fd-6a9602dcd1bf.html'
            '地块',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191105/9fac12db-1b31-4382-9593-dae871c57a4a.html'
            '市民广场',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191108/5f7e2fec-8e81-46a9-bee5-daed11bad30d.html'
            '技术用房',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191108/48a07536-e9df-4100-a017-82010a6d5cde.html'
            '二期东区',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191111/f17b3117-64e5-4d5f-a7bf-7656ff69c966.html'
            '改造升级',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191112/a7dd0006-8f6b-4fc9-8f15-5a8580f32419.html'
            '酒店内装',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191125/720c3f18-d675-4b25-ae78-c877e83b75fa.html
            '骨灰堂',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20190929/1e4d4e0f-b5fd-45d2-8295-bb48774e871e.html'
            '闲置资产',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191112/81948b1a-2c8b-4137-a1a9-145bf6adb8e6.html
            '农贸市场',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191121/64bf4251-ddc9-4c03-b005-0a005772d6f1.html
            '智能产业园',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191127/91979f66-2f86-4c7b-95b1-e27b7d75c8df.html
            '科技产业园',
            '白马镇',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191129/409a0dad-d586-4dc9-947f-5d85f47d53cd.html'
            '办公楼改造',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191202/6011d374-6894-4004-b8d5-f72471352b54.html'
            '七巷安置区',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190929/81247272-c900-433e-b446-80862612696e.html
            '湖新天地',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190929/d3639504-7fc1-44e2-990b-7fad5dfb6c9f.html
            '（土地复垦）',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191119/6e4bb01e-a873-4350-b719-d663a70a431d.html

            # 以下无标段名
            '南堡社区',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191106/7b20477f-f980-4240-9e37-9c8d04682089.html'
            '汽车4S店',
            # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191217/39aa5e65-e954-4b62-adb7-fee29cb400c5.html
            '景致科技大厦',
            # 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20191106/3c552ce6-7c44-43fb-930e-727740a4fd63.html'
            '厂房E区',
        ]
        self.list_bids_section = ['施工.标段', '施工总承包', '施工',
                                  '\(?（?E?P?C?\)?）?总承包',
                                  '装饰装修', '装饰',
                                  '监理',
                                  '设计',
                                  '设备采购', '采购',
                                  '监测及沉降观测',
                                  '城市广场、景观绿化',
                                  '沉降观测',
                                  '材料检测',
                                  '勘察',
                                  '渣土运输处置',
                                  '土建及水电安装', '水电安装',
                                  '装修',
                                  '咨询服务',
                                  '改造']
        self.list_start_with_split_title = [
            '重新招标|重新公告|招标公告|重发公告|重新发布', '[0-9一二三四五六七八九十]*标|[0-9一二三四五六七八九十]*次', ]
        self.list_strips = ['(', ')', '）', "（", '[', ']', '【', '】', '_', '—', '——', '-', '--', '.',
                            '“', '”', "'", '"']
        self.list_anounces = ['招标公告', '中标结果公告', '中标公告', '等资格', '资格后审公告', '后审公告', '资格预审公告', '二次公告', '重新公告', '更正公告',
                              '重发公告',
                              '重新发布']

    def repl_danwei(self, info_dict):
        for i in self.dict_repl_danwei:
            info_dict['html'] = re.sub(i, self.dict_repl_danwei[i], info_dict['html'])
        return info_dict

    def win_bid(self):
        """中标公告"""
        try:
            flag_text = self.sel.xpath('//div[contains(@class,"ewb-trade-right")]/text()').extract_first().strip()
            if flag_text == "无该字段内容" or flag_text == "\\":  # or flag_text == "":
                # # if flag_text == "无该字段内容" or flag_text == "\\" or flag_text == "":
                # with open('./record_no_content.log', 'a+', encoding='utf-8') as f:
                #     f.write(f"##{self.info_dict['count_index']}\t\t##{self.info_dict['origin_url']}\n")
                return {"the_page": "does_not_exist"}
        except:
            pass

        content_root_nodes = self.sel.xpath('//table')
        if not content_root_nodes or "合同编号：<span>HASL-" in self.html or "合同编号：HASL" in self.html:
            # 解决异常情况
            # http://jsggzy.jszwfw.gov.cn/jyxx/003003/003003004/20200121/2b47d88d-c5f9-488c-a555-f45de46617ed.html
            # http://jsggzy.jszwfw.gov.cn/jyxx/003003/003003004/20201202/159b5778-c021-4752-9987-cb2528e37912.html
            content_root_nodes = self.sel.xpath('//body')
        texts = []

        # 遍历所有子节点，获取相应的文本
        for node in content_root_nodes:
            node_text = get_alltext(node)
            texts.append(node_text)

        clean_texts = []
        # 清理文本中的一些空几个，不可见字符，以及加载关键字中间的空格
        for text in texts:
            text = replace_punctuation(re.sub("六、备注(?:.|\n)*", "", text.strip().replace("信息发布时间：", "")))
            text = self.replace_text_dict(text)  # replace
            clean_texts.append(text)

        # 创建状态机
        machine = InfoMachine(self.base_pattern)
        # 执行状态机，解析整个文本
        output_dict = machine.run_list(clean_texts)
        if output_dict == {}:
            output_dict = self.second_match()

        # # **********************debug**************************
        # table_text = """
        # <table id="_Sheet1_6_1" CellPadding="0" CellSpacing="0" style="table-layout: fixed;font-family:SimSun;font-size:9pt;color:#000000;border-collapse:collapse;" border="0" Width="795">	<tr Height="0px" style="font-size: 0px;line-height:0px;">		<td Width="211px" style="border-left:#0000 1px solid;border-right:#0000  1px solid;">&nbsp;</td>		<td Width="213px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td Width="133px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td Width="163px" style="border-right:#0000  1px solid;">&nbsp;</td>		<td Width="75px" style="border-right:#0000 1px solid;">&nbsp;</td>	</tr>	<tr Height="30px">		<td Width='211px' class="A" style="text-align:center">标段名称</td>		<td class="A" style="text-align:center">拟中标单位</td>		<td class="A" style="text-align:center">中标价(元)</td>		<td class="A" style="text-align:center">中标范围和内容</td>		<td style="border-left:#d1e6fa 1px solid;text-align:left;padding:2px;">&nbsp;</td>	</tr>	<tr>		<td Width='211px' class="B">三汊湾闸施工</td>		<td class="B">江苏科弘岩土工程有限公司</td>		<td class="B">453400.00</td>		<td class="B">闸站、涵、隧工程;</td>		<td style="border-left:#d1e6fa 1px solid;text-align:left;padding:2px;">&nbsp;</td>	</tr>	</table>
        # """
        # self.sel = Selector(text=table_text)

        # 获取所有的table表格
        tables = get_all_tables(self.sel)
        for index, table in enumerate(tables):
            text = table.get()
            # print(text)
            # 最后一个空格  导致无法正确进入模式
            # http://jsggzy.jszwfw.gov.cn/jyxx/003003/003003004/20181009/95e9d984-7c2d-40b9-a8c8-78aafd487375.html
            if '<td style="border-left:#d1e6fa 1px solid;text-align:left;padding:2px;"> </td>' in text:
                text = re.sub(r'<td style="border-left:#d1e6fa 1px solid;text-align:left;padding:2px;"> </td>', '',
                              text)
                table = Selector(text=text).xpath("//table")
            result = common_table_extrator(table)
            output_dict = combine_two_dict(output_dict, result)
        html_info_dict = dict_mapping_triedTree(self.info_dict)
        output_dict = combine_two_dict(output_dict, html_info_dict)
        return output_dict

    def second_match(self):
        content_root_nodes = self.sel.xpath('//body')
        texts = []
        # 遍历所有子节点，获取相应的文本
        for node in content_root_nodes:
            node_text = get_alltext(node)
            texts.append(node_text)

        clean_texts = []
        # 清理文本中的一些空几个，不可见字符，以及加载关键字中间的空格
        for text in texts:
            text = replace_punctuation(re.sub("六、备注(?:.|\n)*", "", text.strip().replace("信息发布时间：", "")))
            text = self.replace_text_dict(text)  # replace
            clean_texts.append(text)

        machine = InfoMachine(self.base_pattern)
        # 执行状态机，解析整个文本
        output_dict = machine.run_list(clean_texts)
        return output_dict

    def tender_announcement(self):
        """招标公告"""
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
            if self.info_dict.get('工程所属城市', "") == "镇江市":
                text = re.sub(r'相关部门[:：][\s\S]*', '', text)
            text = self.replace_text_dict(text)  # replace
            clean_texts.append(text)

        # 创建状态机
        machine = InfoMachine(self.base_pattern)
        # 执行状态机，解析整个文本
        output_dict = machine.run_list(clean_texts)

        # 招标->解析表格
        output_dict = self.table_extrator(output_dict)

        html_info_dict = dict_mapping_triedTree(self.info_dict)
        output_dict = combine_two_dict(output_dict, html_info_dict)
        return output_dict

    def table_extrator(self, output_dict):
        if self.info_dict.get('工程所属城市', "") == "镇江市":
            text = re.sub(r'相关部门：[\s\S]*', '', self.html) + "\n</body>\n</html>"
            self.sel = Selector(text=text)
        if self.info_dict.get('工程所属城市', "") in ['镇江市', '苏州市', '盐城市', '扬州市', '常州市', '连云港市', '泰州市', ""]:
            tables = get_all_tables(self.sel)
            if self.info_dict.get('工程所属城市', "") in ['镇江市', '苏州市', ""]:
                table_ori, tables = tables, tables[1:]
                if not tables and len(table_ori) == 1:
                    tables = get_all_tables(self.sel)
            # tables = get_all_tables(Selector(text=text))
            # for table in tables:  # [1:]:
            for index, table in enumerate(tables):  # [1:]:
                if "评审因素" in table.get() and "评审标准" in table.get():  # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20181119/GG_4ff93c3a-2898-4dc4-b73f-2e54de05134f.html
                    continue
                # print(index+1)
                # print(table.get())
                if not table.xpath('.//tr'):
                    table = self._check_tr_exist(table)

                table_result = common_table_extrator(table)
                output_dict = combine_two_dict(output_dict, table_result)
        return output_dict

    def _check_tr_exist(self, table):
        """
            据观测发现，如果没有tr,一定有一个thead和tbody
                http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20201123/4736d648-29d8-4f17-88fa-679599fcaf95.html
                http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20201123/4736d648-29d8-4f17-88fa-679599fcaf95.html
        """
        text = table.get()
        if self.info_dict.get('工程所属城市', "") in ["镇江市", ]:
            if "标段" in text:
                text = text.replace('工期', '招标工期').replace('标段编号', '招标标段编号').replace('估算价', '招标估算价'). \
                    replace('设计周期', '招标工期').replace('工程名称', '标段名称').replace('发包内容', '标段名称')
                # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20191014/c5f54604-ddeb-4126-b0aa-199c79cd0d54.html
            if not table.xpath('.//tr') and "招标标段编号" in text:
                text = text.replace('thead', 'tr').replace('tbody', 'tr')
            sel = Selector(text=text)
            table = sel.xpath("./table")
        return table

    def replace_text_dict(self, text):
        for dict_repl in self.dict_repls:
            text = re.sub(dict_repl, self.dict_repls[dict_repl], text)
        return text

    def handle_especial(self, result, text_all):
        """
            eg:无项目名称，有标段名称
            http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20190929/81247272-c900-433e-b446-80862612696e.html
        """
        re_result = re.findall(r'本招标项目(.*?)\(项目名称\)已由', text_all)
        if re_result:
            result = self.store_project_or_bid_section_name(result, re_result[0]) if self.check_field(result,
                                                                                                      '项目名称') == 2 else result
        return result

    def handle_name(self, result):
        flag = 1
        html = etree.HTML(self.html)
        # if flag and self.info_dict.get('工程所属城市', "") == "南京市":
        if flag:
            ids = [
                ['工程基本信息', '项目名称', 'lblProjectName', 'lblProjectName1'],
                ['工程招标信息', '招标人信息名称', 'lblJianSheDanWei', 'lblJianSheDanWei1'],
            ]
            for id in ids:
                try:
                    txt = html.xpath(f'//span[@id="{id[2]}"]/text()')
                    if not txt:
                        txt = html.xpath(f'//span[@id="{id[3]}"]/text()')
                    if id[1] == "项目名称":
                        flag, result = self.handle_title(txt[0], result, flag)
                    else:
                        if id[1] == '招标人信息名称':
                            result[id[0]].update({id[1]: [txt[0]]})
                        else:
                            result[id[0]].update({id[1]: txt[0]})
                except:
                    pass  # 不做处理，接着走下面逻辑

        text_all = "".join(html.xpath("//text()"))
        if flag:
            txt = re.findall("规定，(.*?)的(.*?)评标工作已经",
                             text_all.replace("\n", "").replace(" ", "").replace('\t', '').replace(" ", ''))
            if txt:
                zb_name, title = txt[0]
                result['工程招标信息'].update({'招标人信息名称': [zb_name]})
                flag, result = self.handle_title(title, result, flag)

        if flag and "中标公告" in self.info_dict['公告标题']:
            flag, result = self.handle_title(self.info_dict['公告类型'][:-6], result, flag)

        if flag and "<strong>" in self.html:
            """第三个strong不是  http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20200512/3210001010404020200512000004.html"""
            strongs = html.xpath('//strong/text()')[0:2]
            if len(strongs) == 2:
                result['工程基本信息'].update({'项目名称': strongs[0]})
                result['工程招标信息'].update({'标段名称': strongs[1]})
                flag = 0

        if flag:
            """
            http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20200323/fb051dc8-96cd-45a6-aa73-47809653841c.html
            http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20200323/63b37fb0-18fa-4e55-83c9-6f9de9103ef9.html
            http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001008/20200323/b8dbd7a3-e104-48d6-b6ed-11f4775272b3.html
            """
            txt = re.findall("规定，(.*?)评标工作已经",
                             text_all.replace("\n", "").replace(" ", "").replace('\t', '').replace(" ", ''))
            if txt:
                title = txt[0]
                flag, result = self.handle_title(title, result, flag)

        if self.check_field(result, "项目名称") == 2:
            flag, result = self.handle_title(self.info_dict['公告标题'], result, flag)

        check_field_projectname = self.check_field(result, '项目名称')
        if check_field_projectname == 2:
            result = self.store_project_or_bid_section_name(result, self.info_dict['公告标题'])
            # result = self.store_project_or_bid_section_name(result, self.info_dict['公告标题'], False)
        # elif not check_field_bidname and check_field_projectname == 2:
        #     result = self.store_project_or_bid_section_name(result, self.info_dict['公告标题'])
        # elif check_field_bidname == 2 and not check_field_projectname:
        #     result = self.store_project_or_bid_section_name(result, result['工程基本信息']['项目名称'], False)
        # msg = f"{str(self.info_dict['count_index'])} \n{result['工程招标信息']['标段名称']}\n{result['工程基本信息']['项目名称']}\n{self.info_dict['公告标题']}\t{self.info_dict['origin_url']}"
        # savelog(LogStateString.Info_NormalRecord, msg=msg)
        return result

    def handle_title(self, title, result, flag):
        # 1) bc 切分项目名/标段名:通过关键字切分
        # 针对项目和工程同时在的情况
        if "工程" in title and "项目" in title:
            index_one = title.index("工程")
            index_two = title.index("项目")
            index = index_one if index_one < index_two else index_two
            result = self.store_project_or_bid_section_name(result, title[0:index + 2]) if self.check_field(result,
                                                                                                            '项目名称') == 2 else result
            result = self.store_project_or_bid_section_name(result, title[index + 2:], False) if self.check_field(
                result, '标段名称') == 2 else result
            flag = 0

        if flag:
            index = -100
            for i, obj in enumerate(self.list_obj_strs):
                if obj in title:
                    index = title.index(obj[-1])
                if index != -100:
                    if not index:
                        if "工程基本信息" in result and "项目名称" not in result['工程基本信息']:
                            result['工程基本信息'].update({'项目名称': title})
                    else:
                        result = self.store_project_or_bid_section_name(result, title[0:index + 1]) if self.check_field(
                            result, '项目名称') == 2 else result
                        result = self.store_project_or_bid_section_name(result, title[index + 1:],
                                                                        False) if self.check_field(result,
                                                                                                   '标段名称') == 2 else result
                    flag = 0
                    break
        # 2) 通过列举标段名区分
        if flag:
            for bid in self.list_bids_section:
                res = re.findall(rf'{bid}', title)
                if res:
                    index = title.index(res[-1])
                    result = self.store_project_or_bid_section_name(result, title[:index]) if self.check_field(result,
                                                                                                               '项目名称') == 2 else result
                    result = self.store_project_or_bid_section_name(result, title[index:], False) if self.check_field(
                        result, '标段名称') == 2 else result
                    flag = 0
                    break

        if not self.check_field(result, '项目名称') and result['工程基本信息']['项目名称'] == '':
            del result['工程基本信息']['项目名称']
            flag = 1
        return flag, result

    def get_null_value(self, result, key):
        result.update({key: {}}) if key not in result else ''
        return result

    def handle_zhaobiao_bid(self, result):
        if '工程招标信息' in result and '标段名称' in result['工程招标信息'] \
                and result['工程招标信息']['标段名称'][-4:] == "招标公告":
            result['工程招标信息'].update({'标段名称': result['工程招标信息']['标段名称'][0:-4]})
        return result

    def check_flag(self, result):
        flag = 0
        needs = [['工程基本信息', '项目名称'], ['工程招标信息', '标段名称']]
        for need in needs:
            if need[0] not in result:
                flag = 1
            elif need[1] not in result[need[0]]:
                flag = 1
        return flag

    def store_project_or_bid_section_name(self, result, name, project_name_store=True):
        name = self.standlize_name(name)

        for n in self.list_start_with_split_title:
            re_result = re.findall(rf'{n}', name)
            index = -1
            if re_result:
                for res in re_result:  # 多匹配
                    index = 0 if not name.index(res) else -1
            if not index:
                name = self.standlize_name(self.info_dict['公告标题'])

        name = self.handle_pre(name)
        if project_name_store:
            result['工程基本信息'].update({'项目名称': name})
        else:
            if name in ['项目', '.', '']:
                name = self.standlize_name(self.info_dict['公告标题'])
            result['工程招标信息'].update({'标段名称': name})
        return result

    def handle_pre(self, name):
        """
        格式化
        :param name:
        :return:
        """
        name = name.strip()
        for strip in self.list_strips:
            name = name.strip(f'{strip}').strip()
        return name

    def handle_zhaobiao_zishen_title(self, result):
        flag = 1
        html = etree.HTML(self.html)
        text_all = "".join(html.xpath("//text()")).replace('（', '(').replace('）', ')')
        if "项目名称/工程名称" in text_all or '标段招标公告' in text_all or '施工招标公告' in text_all or '项目名称及标段' in text_all:
            re_pattern = [
                r'(.*)\(?项目名称/工程名称\)?(.*?)标段招标',
                r'(.*)项目名称(.*?)标段(施工)?招标公告',  # 这里的施工可能为一组，但是不影响[1][2]的取值
                # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20201015/234240e2-7715-407b-a717-f3b4f6d26a09.html
                r'(.*)\(?项目名称/工程名称\)(.*?)\(项目名称及标段\)',
                r'(.*)项目名称(.*)标段\(标段名称\)施工招标公告',
            ]
            for index, pattern in enumerate(re_pattern):
                re_result = re.findall(pattern, text_all)
                if re_result:
                    if self.check_field(result, '项目名称') == 2:
                        result = self.store_project_or_bid_section_name(result,
                                                                        re_result[0][0].strip().strip('(').split('\t')[
                                                                            -1])
                    if self.check_field(result, '标段名称') == 2:
                        result = self.store_project_or_bid_section_name(result, re_result[0][1].strip(')').strip(),
                                                                        False)
                    flag = 0
                    break

            if flag:
                # http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20201023/8a948601-3742-46bd-a4d1-dbc4d0409b08.html
                re_result = re.findall(r'(.*)\(?项目名称及标段', text_all)
                if re_result:
                    title = re_result[0].strip().strip('(').split('\t')[-1]
                    flag, result = self.handle_title(title, result, flag)
        if flag and self.check_field(result, '项目名称') == 2:
            re_result = re.findall(r'本招标项目(.*)\n{0,2}\(?项目名称\)? {0,3}已由', text_all)
            # 兼容带\n的 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20200323/2ffdffe6-0c04-4238-8727-b7fd053490ea.html'
            if re_result:
                result = self.store_project_or_bid_section_name(result, re_result[0])

        if flag and self.check_field(result, '项目名称') == 2:
            re_result = re.findall(r'本招标项目(.*)已由', text_all)
            if re_result:
                result = self.store_project_or_bid_section_name(result, re_result[0])

        if flag and self.check_field(result, '项目名称') == 2:
            re_result = re.findall(r'(.*)已由', text_all)
            if re_result:
                result = self.store_project_or_bid_section_name(result, re_result[0])

        if flag:
            flag, result = self.handle_title(self.info_dict['公告标题'].strip(')').strip('）'), result, 1)

        #  收尾处理
        if not self.check_field(result, '标段名称') and result['工程招标信息']['标段名称'] == "的":
            result = self.store_project_or_bid_section_name(result, '', project_name_store=False)

        check_field_bidname = self.check_field(result, '标段名称')
        check_field_projectname = self.check_field(result, '项目名称')
        if not check_field_bidname and result['工程招标信息']['标段名称'] == '':
            result = self.store_project_or_bid_section_name(result, self.info_dict['公告标题'], False)
            check_field_bidname = 0
        if self.check_field(result, '项目名称') == 2 and self.check_field(result, '标段名称') == 2:
            result = self.store_project_or_bid_section_name(result, self.info_dict['公告标题'])
            result = self.store_project_or_bid_section_name(result, self.info_dict['公告标题'], False)
        elif not check_field_bidname and check_field_projectname == 2:
            result = self.store_project_or_bid_section_name(result, self.info_dict['公告标题'])
        elif check_field_bidname == 2 and not check_field_projectname:
            result = self.store_project_or_bid_section_name(result, result['工程基本信息']['项目名称'], False)
        """本地测试用"""
        # msg = f"{str(self.info_dict['count_index'])} \n{result['工程招标信息']['标段名称']}\n{result['工程基本信息']['项目名称']}\n{self.info_dict['公告标题']}\t{self.info_dict['origin_url']}"
        # savelog(LogStateString.Info_NormalRecord, msg=msg)
        return result

    def check_field(self, result, field_name):  # 可以用eval优化
        flag_num = 0  # exist
        field_dict = {
            '标段名称': ['工程招标信息', '标段名称'],
            '项目名称': ['工程基本信息', '项目名称'],
            '未知工期': ['未知', '未知工期'],
            '中标工期': ['工程投标信息', '中标工期'],
            '中标候选人名称': ['工程投标信息', '中标候选人名称'],
            '中标信息名称': ['工程投标信息', '中标信息名称'],
            "投标报价": ["工程投标信息", "投标报价"],
        }
        value = field_dict[field_name]
        if value[0] not in result:
            flag_num = 1
        elif value[1] not in result[value[0]]:
            flag_num = 2
        return flag_num

    def standlize_name(self, ori_name):
        name = self.handle_pre(ori_name)

        return_name = None
        name = name if not name.startswith('的') else name[1:]
        for anounce in self.list_anounces:
            if anounce in name:
                return_name = name[:name.index(anounce)]
                break
        if return_name == '' and ori_name != self.info_dict['公告标题']:
            return_name = self.standlize_name(self.info_dict['公告标题'])
        elif return_name == '' and ori_name == self.info_dict['公告标题']:
            return_name = self.info_dict['公告标题']

        return return_name if return_name else name

    def handle_project_time(self, result, index=1):
        if index == 1:
            result['工程投标信息']['中标工期'] = result['未知']['未知工期']
            del result['未知']['未知工期']
            if result['未知'] == {}:
                del result['未知']
        elif index == 2:
            result['工程投标信息']['中标信息名称'] = result['工程投标信息']['中标候选人名称']
            del result['工程投标信息']['中标候选人名称']
        return result

    def final_deal(self, result):
        if self.check_flag(result) and 'the_page' not in result:
            result = self.handle_name(result)
        if self.check_field(result, "未知工期") == 0 and self.check_field(result, "中标工期") == 2:
            result = self.handle_project_time(result)
        if self.check_field(result, "中标候选人名称") == 0 and self.check_field(result, "中标信息名称") == 2:
            result = self.handle_project_time(result, 2)
        if self.check_field(result, '中标信息名称') == 2:
            re_result = re.findall(r"第一名：(.*?)<", self.html)
            if re_result:
                result['工程投标信息']['中标信息名称'] = re_result[0]
        #
        return result

    # def write(self, name, info):
    #     with open(f'./record_log_{name}.log', 'a+', encoding='utf-8') as f:
    #         f.write(info)

    def start_parse(self) -> dict:
        result = {}
        """本地测试"""
        print(self.info_dict['origin_url'])
        # if self.info_dict[
        #     'origin_url'] == 'http://jsggzy.jszwfw.gov.cn/jyxx/003003/003003004/20181029/ccaae207-ca54-4c14-93a8-4ed8fbafef71.html':
        #     self.write(1, self.info_dict)
        #     # "公告类型": "中标结果公告",
        #     # "工程类型": "水利工程",
        #     # "count_index": 3
        # if self.info_dict[
        #     'origin_url'] == 'http://jsggzy.jszwfw.gov.cn/jyxx/003002/003002001/20190509/c4eac300-fe6f-4e13-9309-b21ecf63dc3a.html':
        #     self.write(2, self.info_dict)
        #     # "公告类型": "招标公告",
        #     # "工程类型": "交通工程",
        #     # "count_index": 913
        # if self.info_dict[
        #     'origin_url'] == 'http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20191025/6e97f0a9-2467-43c1-81f1-4efa46d4a1fb.html':
        #     self.write(3, self.info_dict)
        #     # "公告类型": "招标公告/资审公告",
        #     # "工程类型": "建设工程 ",
        #     # "count_index": 5426

        if self.info_dict["公告类型"] == "中标结果公告" or self.info_dict["公告类型"] == "中标公告":
            result = self.win_bid()
            self.get_null_value(result, "工程基本信息")
            self.get_null_value(result, "工程招标信息")
            result = self.final_deal(result)


        elif self.info_dict["公告类型"] in ["招标公告/资审公告", '招标公告']:
            result = self.tender_announcement()
            self.get_null_value(result, "工程基本信息")
            self.get_null_value(result, "工程招标信息")
            if self.check_flag(result):
                result = self.handle_zhaobiao_zishen_title(result)
            # 招标公告中不可能有报价
            if not self.check_field(result, '投标报价'):
                del result['工程投标信息']['投标报价']
        pprint(result)
        return result


'''
http://jsggzy.jszwfw.gov.cn/jyxx/003002/003002001/20190509/c4eac300-fe6f-4e13-9309-b21ecf63dc3a.html
logger_utils.py[:75]-Waring_WeiZhiKeyWords#未知邮箱:['651123911@qq.com']#

http://jsggzy.jszwfw.gov.cn/jyxx/003001/003001001/20191025/6e97f0a9-2467-43c1-81f1-4efa46d4a1fb.html
#招标人信息邮箱:wxzt@vip.163.com	



'''
