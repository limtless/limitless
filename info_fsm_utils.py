from regular_matching_rules import get_keywordTredTree_instance
from spidertools.utils.text_utils import replace_punctuation
from spidertools.utils.re_utils import match_one
from configs.commom import db_table_list

import re


def clean_triedtree_keys(text):
    triedTree = get_keywordTredTree_instance()
    node_text = replace_punctuation(text.strip())
    #clean_text = replace_punctuation(node_text.replace(" ", "").replace(" ", ""))  # nbsp就是那些没用的字符
    clean_text  = replace_punctuation(re.sub(r"[\s ]*(\([^\(]*?\)){0,1}[\s ]*", "", node_text))

    keywords, types, _ = triedTree.process(clean_text)
    for keyword in keywords:
        search_keyword = []
        for k in keyword:
            search_keyword.append(k)
            search_keyword.append("[\s ]*(\([^\(]*?\)){0,1}[\s ]*")  # nbsp不换行空格
        search_keyword = "".join(search_keyword) + ":"
        replace_keyword = keyword + ":"
        node_text = re.sub(search_keyword, replace_keyword, node_text)
    return node_text


def get_valid_parsedmode_value(key, type_list, text):
    '''
    获取到有效的parsedMode关键词
    满足以下两种情况就可以算是有效的parseMode:
    key后面接一个冒号  key:
    key前面接数字和顿号或者点号    二、key
    '''
    mode_value = ""
    for sub_key in type_list:
        parts = sub_key.split("_")
        if parts[0] == "parsemode":
            # 按理每个词条只能匹配出一个parsemode
            mode_value = parts[1]
            break

    if mode_value:
        if key + ":" in text:
            pass
        else:
            regex_string = "[\\d一二三四五六七八九十]{1,2}?\s*[、|\.]\d{0,2}\\s*" + key
            match = re.search(regex_string, text)
            if match:
                pass
            else:
                mode_value = ""
    return mode_value


def filter_unused_keys(text, keywords, types, end_positions, base_regex=None):
    '''
    过滤掉一些没有用的key值,包括正则匹配没有或者为空的key值
    :return:
    '''
    filter_keywords = []
    filter_types = []
    filter_regex_values = []
    filter_modes = []

    """z_:获取每个keyword正则范围"""
    keyword_start_positions = [i - len(j) for i, j in zip(end_positions, keywords)]
    regex_end_positions = keyword_start_positions[1:] + [len(text)]
    previewkey_end_positions = [0] + end_positions[:-1]
    if not base_regex:
        for key, type, start_position, end_position in zip(keywords, types, keyword_start_positions,
                                                           regex_end_positions):
            if key == text:
                filter_keywords.append(key)
                filter_types.append(type)
                filter_regex_values.append(key)
                filter_modes.append("")
    else:
        filter_start_positions = []
        for key, type, start_position, end_position, previewkey_end_position in zip(keywords, types,
                                                                                    keyword_start_positions,
                                                                                    regex_end_positions,
                                                                                    previewkey_end_positions):
            if 'ignore' in type:
                continue

            keyword_mode = get_valid_parsedmode_value(key, type, text[previewkey_end_position:end_position])
            if not keyword_mode:
                regex_key_start = key + ":"
                ttruncted = text[start_position:end_position]
                if regex_key_start not in ttruncted:
                    continue

            filter_keywords.append(key)
            filter_types.append(type)
            filter_modes.append(keyword_mode)
            filter_start_positions.append(start_position)
        filter_end_positions = filter_start_positions[1:] + [len(text)]


        for key, start_position, end_position in zip(filter_keywords,
                                                           filter_start_positions,
                                                           filter_end_positions):
            ttruncted = text[start_position:end_position]
            regex_key = base_regex % key
            keyword_regex_match_str = match_one(regex_key, ttruncted)
            filter_regex_values.append(keyword_regex_match_str)

    return filter_keywords, filter_types, filter_regex_values, filter_modes


def get_triedtree_result(text, base_regex):
    output_result = []
    triedTree = get_keywordTredTree_instance()
    keywords, types, end_positions = triedTree.process(text)
    filter_keywords, filter_types, filter_regex_values, filter_modes = filter_unused_keys(text, keywords, types,
                                                                                          end_positions, base_regex)
    if len(filter_modes) == 2:
        if '招标人信息' in filter_modes and '招标代理机构' in filter_modes:
            filter_modes = ["招标人和招标代理人信息" for i in filter_modes if i == "招标人信息" or i == "招标代理机构"]
    elif len(filter_modes) > 2:
        need_change_index = []
        for index, (i, j) in enumerate(zip(filter_modes[:-1], filter_modes[1:])):
            if i == "招标人信息" and j == '招标代理机构':
                need_change_index.append(index)

        for index in need_change_index:
            filter_modes[index] = "招标人和招标代理人信息"
            filter_modes[index + 1] = '招标人和招标代理人信息'
    for key, typelist, filter_value, filter_mode in zip(filter_keywords, filter_types, filter_regex_values,
                                                        filter_modes):
        result = {}
        result['mode'] = filter_mode
        result['explicit_type'] = {}
        result['common_type'] = {}

        if filter_value:
            for sub_key in typelist:
                parts = sub_key.split("_")
                if parts[0] in db_table_list:
                    db_key = parts[0] + "-" + parts[1]
                    result['explicit_type'][db_key] = filter_value
                elif parts[0] == 'common':
                    db_key = parts[1]
                    result['common_type'][db_key] = filter_value
        if check_dictvalue(result):
            output_result.append(result)
    return output_result


def check_dictvalue(dict_obj):
    valid = False
    if dict_obj:
        for key, value in dict_obj.items():
            if value:
                valid = True
                break
    return valid


def split_texts(text):
    text_lists = text.split('\r\n')
    text_lists = [t.strip() for t in text_lists if t.strip() != ""]
    return text_lists


def conbine_contract_and_agent_mode(item_list):
    for index, (before, after) in enumerate(zip(item_list[:-1], item_list[1:])):
        if before['mode'] == "招标人信息" and after['mode'] == '招标代理机构':
            before['mode'] = "招标人和招标代理人信息"
            after['mode'] = "招标人和招标代理人信息"


if __name__ == '__main__':
    if __name__ == '__main__':
        text = '''任。'''
        text = clean_triedtree_keys(text)
        print(text)
