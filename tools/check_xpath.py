from scrapy.selector import Selector
import pymongo
import json


def start_parse(source_type, notice_type, xpath_list):
    search_dict = {}
    search_dict['source_type'] = source_type
    search_dict['公告类型'] = notice_type
    xpath_list = xpath_list

    xpath_client = pymongo.MongoClient('192.168.2.181', 27017)
    html_list = []  # 待检测的网页
    data = xpath_client.construction.project_html.find(search_dict)

    for item in data:
        html = {}
        html['网址'] = item['origin_url']
        html['源码'] = item['html']
        html_list.append(html)
    return check_xpath(html_list, xpath_list)


def check_xpath(html_list, xpath_list):
    for html in html_list:
        origin_url = str(html['网址'])
        HTML = html['源码']
        if is_json(HTML):
            # print('这是json网页' + origin_url)
            pass
        else:
            result_list = []
            html = Selector(text=HTML)
            for xpath in xpath_list:
                result = html.xpath(xpath)
                if result:  # 如果检索到的内容不为空
                    result_list.append(result)
                else:
                    pass
            if result_list:  # 能正常解析，网页格式相同
                pass
            else:
                print('该网页格式不同，网址为：' + origin_url)  # 输出xpath格式未知的网页
                break


def is_json(HTML):  # 判断是不是json格式的网页，是返回True,不是返回False
    html_or_json = rf"""{HTML}"""
    try:
        json.loads(html_or_json)
    except Exception as e:
        return False
    return True


if __name__ == '__main__':
    xpath_list = [
        '//*[@id="prjectTable"]',
        "//div[@class='detail_con']"
    ]  # 传入要解析验证的xpath
    start_parse("江苏省公路水路建设市场信用信息服务系统", "招标公告", xpath_list)
