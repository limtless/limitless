from scrapy.selector import Selector
from configs.commom import  get_pagetype,PageType,DBTableInfo
from spidertools.utils.xpath_utils import get_alltext
from spidertools.utils.text_utils import remove_nouse_letters,replace_punctuation,clean_html_whitesplace
from spidertools.utils.snippets import combine_two_dict
from info_fsm import InfoMachine


from table_info_extract.extract_utils import table_info_extract_styleone
from table_info_extract import dict_mapping_triedTree

class SuZhouZhengFuCaiGouWang(object):
    def __init__(self,info_dict):
        self.html = info_dict['html']
        self.sel = Selector(text=self.html)
        self.base_pattern = '%s:(\S*)'
        self.info_dict = info_dict

    def get_tab_ids(self):
        output_dict = {}
        tab_nodes  = self.sel.xpath("//*[@id='menu']/li/a")
        for node in tab_nodes:
            tab_id = node.xpath("./@href").extract()[0]
            tab_id = tab_id.split("#")[1]
            tab_text = node.xpath("./text()").extract()[0].strip().replace(" ","")
            if '暂无' not in tab_text:
                output_dict[tab_id] = tab_text

        return output_dict



    def parse_bidding_announcemen(self,root):
        '''
        投标信息提取
        :return:
        '''
        return {}

    def parse_bid_announcemen(self,root):
        '''
        招标信息提取
        :param root:
        :return:
        '''

        text_list = []
        p_texts = root.xpath('.//p[@class="MsoNormal"]')
        if len(p_texts):
            for p in p_texts:
                texts_node = p.xpath(".//text()").extract()
                text_str = ""
                for text in texts_node:
                    text_str += text
                text_list.append(text_str)
        else:
            p_texts = root.xpath('.//div[@class="Article"]/p')
            for p in p_texts:
                texts_node = p.xpath(".//text()").extract()
                #text_str = ""
                # 布局参考http://czju.suzhou.gov.cn/zfcg/html/project/0db3d17db3454b57a84686fe136e4e6f.shtml
                for text in texts_node:
                    #text_str += text
                    text_list.append(text)


        machine = InfoMachine(self.base_pattern)
        clean_texts = []
        for text in text_list:
            text = replace_punctuation(text)
            text = clean_html_whitesplace(text)
            clean_texts.append(text)

        output = machine.run_list(clean_texts)

        return output


    def parse_win_bid_announcemen(self,root):
        '''
        中标信息提取
        :param root:
        :return:
        '''

        text_list = []
        p_texts = root.xpath('.//p[@class="MsoNormal"]')
        for p in p_texts:
            texts_node = p.xpath(".//text()").extract()
            text_str = ""
            for text in texts_node:
                text_str += text
            text_list.append(text_str)

        machine = InfoMachine(self.base_pattern)
        clean_texts = []
        for text in text_list:
            text = replace_punctuation(text)
            text = clean_html_whitesplace(text)
            clean_texts.append(text)

        output = machine.run_list(clean_texts)
        return  output





    def start_parse(self):
        # 第一步，获取所有的tap页状态，如果有暂无，就可以pass掉
        output_list = []
        if self.info_dict['construction_type'] != "工程类":
            return output_list
        table_info = self.get_global_table_info()
        tabs_dict = self.get_tab_ids()
        for key,value in tabs_dict.items():
            pagetype = get_pagetype(value)
            if pagetype  == None:
                continue
            tab_info_node = self.sel.xpath('//*[@id="%s"]' % key)
            if tab_info_node:
                first_node = tab_info_node[0]
                result = self.prase_announcement_info(first_node,pagetype)
                part_result = {}
                if pagetype == PageType.BIDDING_ANNOUNCEMEN:
                    part_result = self.parse_bidding_announcemen(first_node)
                elif pagetype == PageType.BID_ANNOUNCEMENT:
                    part_result = self.parse_bid_announcemen(first_node)
                elif pagetype == PageType.WIN_BIDDING_ANNOUNCEMENT:
                    part_result = self.parse_win_bid_announcemen(first_node)
                combine_two_dict(result,part_result)
                combine_two_dict(result,table_info)
                output_list.append(result)
        return output_list



    def parse_bid_pages(self):
        pass


    def prase_announcement_info(self,root,page_type):
        '''
        获取公告标题和发布时间
        :return:
        '''
        result_dict = {}
        result_dict[DBTableInfo.PROJECT_ANNOUNCEMENT] = {}
        title = root.xpath(".//div[@class='M_title']/text()").extract()
        if title:
            result_dict[DBTableInfo.PROJECT_ANNOUNCEMENT]["名称"]  = remove_nouse_letters(title[0])

        release_node = root.xpath(".//div[@class='date']")
        if release_node:
            release_str = remove_nouse_letters(get_alltext(release_node[0]))
            release_str = replace_punctuation(release_str)
            release_str = clean_html_whitesplace(release_str)
            machine = InfoMachine(self.base_pattern)
            machine.current_state = machine.states['工程公告信息']
            output = machine.run_list([release_str])
            result_dict = combine_two_dict(result_dict,output)

        result_dict[DBTableInfo.PROJECT_ANNOUNCEMENT]["公告类型"] = page_type

        return result_dict


    def get_global_table_info(self):
        '''
        解析公告页面最顶端的table里面的内容
        :return:
        '''
        table_node = self.sel.xpath("//table[@class='D_tableBox']")[0]
        info_dict = table_info_extract_styleone(table_node)

        info_dict = dict_mapping_triedTree(info_dict)

        return info_dict









if __name__ == '__main__':
    demo_html_path = r'F:\工作相关文档\爬虫相关\company_info_extrator\demo_html\苏州市政府采购.html'
    url = 'http://czju.suzhou.gov.cn/zfcg/html/project/f5f5423ef1254bdeab4a0939574b240c.shtml'
    htm_str = ""
    with open(demo_html_path,'r',encoding='utf-8') as fread:
        htm_str = fread.read()



    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded;",
        "charset": "UTF-8",
        "Host": "czju.suzhou.gov.cn",
        "Origin": "http://czju.suzhou.gov.cn",
        "Proxy-Connection": "keep-alive",
        "Referer": "http://czju.suzhou.gov.cn/zfcg/html/search.shtml?type=&title=&choose=&projectType=0&zbCode=&appcode=",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    import requests
    req = requests.get(url,headers=headers)
    info = {}
    info['html'] = req.text
    info['construction_type'] = "工程类"
    extor_obj = SuZhouZhengFuCaiGouWang(info)
    from pprint import pprint
    result = extor_obj.start_parse()

    pprint(result)
    import os
    import json
    if result:
        save_file = "url_2_json.txt"
        if os.path.exists("url_2_json.txt"):
            with open(save_file,'r',encoding='utf-8') as fread:
                json_obj = json.load(fread)
                temp_json = {}
                temp_json[url] = result
                isin = False
                for index, item in enumerate(json_obj["items"]):
                    if url  in item:
                        isin = True
                        break
                if isin:
                    answer = input("已经存在,请确认（输入任意值继续）")

                    json_obj["items"].pop(index)
                json_obj['items'].append(temp_json)
            with open(save_file, 'w',encoding='utf-8') as file_obj:
                json.dump(json_obj, file_obj)




        else:
            json_obj = {}
            json_obj['model_path'] = 'extractors.commonresources.jiangsu.suzhou.suzhouzhengfucaigouwang.SuZhouZhengFuCaiGouWang'
            json_obj['source_name'] = '苏州市政府采购网'
            json_obj['items'] = []
            temp_json = {}
            temp_json[url] = result
            json_obj['items'].append(temp_json)

            with open(save_file, 'w',encoding='utf-8') as file_obj:
                json.dump(json_obj, file_obj)