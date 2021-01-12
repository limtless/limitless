from utils.logger_utils import savelog ,LogStateString
from project_setting import DEBUG,MongoUrl
from spidertools.utils.pinyin_utils import pinyin
from spidertools.db_utils.mongdb_utils import get_mongo_connect
from spidertools.utils.mutiprocess_utils import parallel_apply
from spidertools.utils.time_utils import get_current_datetime
import pydoc

import traceback




def make_some_extra_info(output_dict,origin_dict):
    output_dict["原始地址"] = origin_dict['origin_url']
    output_dict['公告类型'] = output_dict['工程公告信息']["公告类型"]
    output_dict["工程公告信息发布时间"] = output_dict['工程公告信息']["工程公告信息发布时间"]
    output_dict["is_parsed"] = 0
    output_dict['search_key'] = origin_dict['origin_url'] + "$$" + origin_dict['公告类型'] + "$$" + output_dict["工程公告信息发布时间"]

def extor_info_worker(info_dict):
    '''
    解析网页的worker
    :param info_dict:
    :return:
    '''
    try:
        module_list = ["extractors",'commonresources']
        if 'province' in info_dict:
            module_list.append(pinyin(info_dict['province']))
        #if 'city' in info_dict:
        #    module_list.append(pinyin(info_dict['city']))
        module_list.append(pinyin(info_dict['source_type']))
        module_list.append(pinyin(info_dict['source_type'],upper_first_char=True))

        full_class_name = ".".join(module_list)

        obj = pydoc.locate(full_class_name)(info_dict)
        output = obj.output_extractor_dict()


        if type(output) == list:
            for item in output:
                make_some_extra_info(item,info_dict)
        elif type(output) == dict:
            make_some_extra_info(output,info_dict)
    except Exception as e:
        if "html" in info_dict:
            del info_dict['html']
        if "_id" in info_dict:
            del info_dict["_id"]
        savelog(LogStateString.FatalError,traceback.format_exc(),msg_dict=info_dict)
        output = None
    return output

def parse_callback(insert_item):
    '''处理信息提取的结果'''
    mongo_extor_table = mongo_db['project_info_dict']
    if insert_item:
        if not DEBUG:
            mongo_table.update({"origin_url":insert_item['原始地址']}, { "$set":{"is_parsed":1} })

        if type(insert_item) == list:
            for item in insert_item:
                search_dict = {"search_key": item['search_key']}
                search_result = mongo_extor_table.count_documents(search_dict)
                if search_result:
                    item['update_time'] = get_current_datetime()
                    update_value = {"$set": item}
                    mongo_extor_table.update_one(search_dict, update_value)
                else:
                    item['create_time'] = get_current_datetime()
                    item['update_time'] = get_current_datetime()
                    mongo_extor_table.insert_one(item)
        else:
            search_dict = {"search_key": insert_item['search_key']}
            search_result = mongo_extor_table.find(search_dict).count()
            if search_result:
                insert_item['update_time'] = get_current_datetime()
                update_value = {"$set": insert_item}
                mongo_extor_table.update_one(search_dict, update_value)
            else:
                insert_item['create_time'] = get_current_datetime()
                insert_item['update_time'] = get_current_datetime()
                mongo_extor_table.insert_one(insert_item)

        from pprint import pprint
        pprint(insert_item)


def mutiproces_parse(search_condition):
    total_count = mongo_table.find(search_condition).count()
    for i in range(int(total_count/1000) + 1):
        print("第"+str(i+1)+"次开始")
        skip_num = 1000 * i
        items =  mongo_table.find(search_condition).skip(skip_num).limit(1000)
        process_num = 8
        queue_max_num = 10000
        print("start")
        parallel_apply(
            func=extor_info_worker,
            iterable=items,
            workers=process_num,
            max_queue_size=queue_max_num,
            callback=parse_callback,
            dummy=True,
        )




if __name__ == '__main__':
    _, mongo_db = get_mongo_connect(mongo_url="127.0.0.1:27017")
    mongo_table = mongo_db['project_html']

    search_condition = {
        #'is_parsed': 0,
        #'公告类型': "招标公告",  # 成交公告/中标结果公告
        'source_type': "江苏政府采购网"
    }

    mutiproces_parse(search_condition)