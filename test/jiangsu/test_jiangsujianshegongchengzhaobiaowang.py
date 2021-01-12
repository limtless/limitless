from spidertools.db_utils.mongdb_utils import get_mongo_connect
from spidertools.utils.time_utils import get_current_date,get_current_datetime
from spidertools.utils.mutiprocess_utils import parallel_apply
from spidertools.utils.pinyin_utils import pinyin
import pydoc
from pprint import pprint
#'公告类型': "中标结果公告",
#        'source_type':"江苏建设工程招标网"

base_search_conditon = {
        'is_parsed': 0,
        '公告类型': "招标公告",  # 成交公告/中标结果公告
        'source_type': "江苏建设工程招标网"
    }

class BaseTest(object):
    def __init__(self,mongo_url="mongodb://192.168.2.181:27017",mongo_table="project_html",search_condition=base_search_conditon):
        self.mongo_url = mongo_url
        self.mongo_table = mongo_table
        self.search_condition = search_condition

        _, self.mongo_db = get_mongo_connect(mongo_url=self.mongo_url)  # "mongodb://localhost:27017") #
        self.mongo_table = self.mongo_db[self.mongo_table]

    def get_total_count(self):
        return self.mongo_table.find(self.search_condition).count()


    def start_run(self):
        total_count = self.get_total_count()
        print("总条数" + str(total_count))
        for i in range(int(total_count / 3000) + 1):
            # if i ==0:
            #     continue
            print("第" + str(i + 1) + "次开始")
            items = self.mongo_table.find(self.search_condition).limit(3000)
            process_num = 20
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

def extor_info_worker(info_dict):
    '''
    解析网页的worker
    :param info_dict:
    :return:
    '''

    module_list = ["extractors",'commonresources']
    if 'province' in info_dict:
        module_list.append(pinyin(info_dict['province']))
    #if 'city' in info_dict:
    #    module_list.append(pinyin(info_dict['city']))
    module_list.append(pinyin(info_dict['source_type']))
    module_list.append(pinyin(info_dict['source_type'],upper_first_char=True))

    full_class_name = ".".join(module_list)


    obj = pydoc.locate(full_class_name)(info_dict)

    output = obj.start_parse()
    if type(output) == list:
        for item in output:
            item["原始地址"] = info_dict['origin_url']
            item['公告公告类型'] = item['工程公告信息']["公告类型"]
            item["工程公告信息发布时间"] = item['工程公告信息']["工程公告信息发布时间"]
            item["is_parsed"] = 0
            item['search_key'] = info_dict['origin_url'] +"$$" + item['公告公告类型'] + "$$" + item["工程公告信息发布时间"]
    elif type(output) == dict:
        output["原始地址"] = info_dict['origin_url']
        output['公告公告类型'] = output['工程公告信息']["公告类型"]
        output["工程公告信息发布时间"] = output['工程公告信息']["工程公告信息发布时间"]
        output['search_key'] = info_dict['origin_url'] + "$$" + output['公告公告类型'] + "$$" + output["工程公告信息发布时间"]
        output["is_parsed"] = 0
    return output


def parse_callback(item):
    pprint(item)


if __name__ == '__main__':
    test_obj = BaseTest()
    test_obj.start_run()
