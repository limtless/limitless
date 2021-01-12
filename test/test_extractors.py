import json
import pydoc
import requests

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


def test_file(filename):
    with open(filename, 'r', encoding='utf-8') as fread:
        json_obj = json.load(fread)

    model_name = json_obj["model_path"]

    for item in json_obj['items']:
        for key,value in item.items():
            req = requests.get(key,headers=headers)
            info = {}
            info['html'] = req.text
            info['construction_type'] = "工程类"

            try:
                obj = pydoc.locate(model_name)(info)
            except Exception as e:
                print("not exist "+ model_name)

            output = obj.start_parse()

            if output != value:
                print("error")
            else:
                print("Url:"+ key +"   is ok")


if __name__ == '__main__':
    test_file(r"F:\工作相关文档\爬虫相关\company_info_extrator\extractors\commonresources\jiangsu\suzhou\url_2_json.txt")