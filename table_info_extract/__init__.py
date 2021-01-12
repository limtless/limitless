from spidertools.utils.snippets import combine_two_dict,combine_dict_to_list
from regular_matching_rules import get_keywordTredTree_instance
from info_fsm import InfoMachine


def dict_mapping_triedTree(info_dict):
    triedTree = get_keywordTredTree_instance()
    single_item = {}
    for key, value in info_dict.items():
        types = triedTree.get_word_types(key)
        used_types = [type for type in types if
                      not type.startswith("parsemode") and not type.startswith("ignore") and not type.startswith(
                          'table_key')]
        if used_types and value:
            assert len(used_types) == 1
            single_item[used_types[0]] = value

    single_item = convert_triedtree_key_to_json(single_item)
    return single_item



def convert_triedtree_key_to_json(info_dict):
    modes_in_dict = set()
    explict_dict = {"未知":{}}
    common_dict = {}
    for key in info_dict.keys():
        if len(key.split("_")) != 2:
            print(key)
        mode,value_key = key.split("_")
        modes_in_dict.add(mode)
        if mode == 'common':
            common_dict[value_key] = info_dict[key]
        else:
            if mode not in explict_dict:
                explict_dict[mode] = {}
            explict_dict[mode][value_key] = info_dict[key]
    common_type_follow = "未知"
    if "工程投标信息" in modes_in_dict:
        common_type_follow = "工程投标信息"
    explict_dict[common_type_follow] = combine_two_dict(explict_dict[common_type_follow],common_dict)
    return explict_dict


def list_mapping_triedTree(info_list):
    output = {}
    for info  in info_list:
        single_item = dict_mapping_triedTree(info)
        if single_item:
            for key,value in single_item.items():
                if key == "工程投标信息":
                    if key not in output:
                        output[key] = []
                    output[key] = combine_dict_to_list(output[key], single_item[key])
                else:
                    if key not in output:
                        output[key] = single_item[key]
                    else:
                        output[key] = combine_two_dict(output[key],single_item[key])


    return output








if __name__ == '__main__':
    test_list = [{'中标候选人名称': '徐州市政建设集团有限责任公司',
  '企业业绩': '卧牛山山体公园工程一标段,中标2362.25万元,中标时间:2018/10/23。',
  '投标报价': '2529.259609',
  '负责人证号': '00496563',
  '项目负责人': '马慧焰'},
 {'中标候选人名称': '济南城建集团有限公司',
  '企业业绩': '',
  '投标报价': '2505.760565',
  '负责人证号': '',
  '项目负责人': '田慧'},
 {'中标候选人名称': '大千生态环境集团股份有限公司',
  '企业业绩': '',
  '投标报价': '2616.676396',
  '负责人证号': '',
  '项目负责人': '冀春艳'}]


    test_dict = {'中标价': '795.369545',
 '招标代理机构名称': '江苏郁州建设工程有限公司',
 '中标工期': '150',
 '发包类型': '公开招标',
 '工程地点': '响水县大有镇、小尖镇、老舍中心社区、张集中心社区、七套中心社区、六套中心社区',
 '建设单位名称': '响水县灌江控股集团有限公司',
 '招标人定标原因及依据': '根据招标文件中约定的评标办法',
 '标段名称': '响水县七套中心社区现代化智慧农贸市场工程',
 '标段编号': '3209212009100002-BD-001',
 '评标委员会成员': '邱东梅、沈光驹、杨荣娟、王煜、张卫红',
 '项目名称': '响水县现代化智慧农贸市场建设工程',
 '项目类型:': '房屋建筑施工',
 '项目经理姓名': '王伟平',
 '项目编号': '3209212009100002'}


    from pprint import pprint

    #pprint(list_mapping_triedTree(test_list))
    pprint(dict_mapping_triedTree(test_dict))



