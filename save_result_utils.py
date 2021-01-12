import requests
import os
import json
import pydoc
from pprint import pprint


def check_url(info_dict,save_file_name,request_header=None):
    request_url = info_dict['url']
    if request_header:
        req = requests.get(request_url,headers=request_header)
    else:
        req = requests.get(request_url, headers=request_header)
    info_dict['html'] = req.text

    full_class_name = info_dict['model_path']
    try:
        extor_obj = pydoc.locate(full_class_name)(info_dict)
    except Exception as e:
        print("module " + full_class_name + " is not exist")
    result = extor_obj.start_parse()
    pprint(result)

    if result:
        if os.path.exists(save_file_name):
            with open(save_file_name,'r',encoding='utf-8') as fread:
                json_obj = json.load(fread)
                temp_json = {}
                temp_json[request_url] = result
                isin = False
                for index, item in enumerate(json_obj["items"]):
                    if request_url  in item:
                        isin = True
                        break
                if isin:
                    answer = input("已经存在,请确认（输入任意值继续）")
                    json_obj["items"].pop(index)
                json_obj['items'].append(temp_json)
            with open(save_file_name, 'w',encoding='utf-8') as file_obj:
                json.dump(json_obj, file_obj)


        else:
            json_obj = {}
            json_obj['items'] = []
            temp_json = {}
            temp_json[save_file_name] = result
            json_obj['items'].append(temp_json)

            with open(save_file_name, 'w',encoding='utf-8') as file_obj:
                json.dump(json_obj, file_obj)