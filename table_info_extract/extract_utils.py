from spidertools.utils.xpath_utils import get_alltext
from spidertools.utils.text_utils import remove_nouse_letters,replace_punctuation,clean_html_whitesplace,clean_text
from regular_matching_rules import get_keywordTredTree_instance
import re
from enum import Enum

class tableModelEnum(Enum):
    model_one = 0
    model_two = 1
    model_three = 2


def table_info_extract_styleone(table_node):
    '''
        <table>
            <tbody>
                <tr>
                    <th>xxxx</th>
                    <td>xxxx</td>
                    ...
                </tr>

                <tr>
                    <th>xxxx</th>
                    <td>xxxx</td>
                    ...
                </tr>
                ...
            </tbody>
        </table>
    :return:
    '''
    tr_node = table_node.xpath('.//tr')
    result = {}
    for tr in tr_node:
        th_nodes = tr.xpath('.//th')
        td_nodes = tr.xpath('.//td')
        assert len(th_nodes) != td_nodes
        for th,td in zip(th_nodes,td_nodes):
            key_text = th.xpath("./text()").extract()[0]
            value_text = td.xpath("./text()").extract()[0]

            value_text = remove_nouse_letters(value_text)
            value_text = replace_punctuation(value_text)
            value_text = clean_html_whitesplace(value_text)
            key_text = remove_nouse_letters(key_text)
            key_text = replace_punctuation(key_text)
            key_text = clean_html_whitesplace(key_text)

            if key_text and value_text:
                result[key_text] = value_text
    return result


def table_info_extract_styletwo(table_node):
    '''
        <table>
            <tbody>
                <tr>
                    <td>xxxx</td>
                    <td>xxxx</td>
                    ...
                </tr>

                <tr>
                    <td>xxxx</th>
                    <td>xxxx</td>
                    <td>xxxx</th>
                    <td>xxxx</td>
                    ...
                </tr>
                ...
            </tbody>
        </table>
    :return:
    '''
    tr_node = table_node.xpath('.//tr')
    result = {}
    for tr in tr_node:
        td_nodes = tr.xpath('./td')
        if td_nodes and len(td_nodes)%2 == 0:
            for index in range(int(len(td_nodes)/2)):
                key_text = clean_html_whitesplace(get_alltext(td_nodes[2*index]))
                value_text = clean_html_whitesplace(get_alltext(td_nodes[2*index+1]))

                value_text = remove_nouse_letters(value_text)
                value_text = replace_punctuation(value_text)
                value_text = clean_html_whitesplace(value_text)

                key_text = remove_nouse_letters(key_text)
                key_text = replace_punctuation(key_text)
                key_text = clean_html_whitesplace(key_text)

                if key_text and value_text:
                    result[key_text] = value_text
    return result



def table_info_extract_stylethree(table_node):
    '''
        <table>
            <tbody>
                <tr>
                    <td>key1</th>
                    <td>key2</td>
                    <td>key3</td>
                    ...
                </tr>

                <tr>
                    <td>value1</th>
                    <td>value2</td>
                    <td>value3</th>
                    ...
                </tr>
                ...
            </tbody>
        </table>
    :return:
    '''
    tr_nodes = table_node.xpath('.//tr')
    result = {}
    if len(tr_nodes) == 2:
        tr_one,tr_two = tr_nodes
        for td_one,td_two in zip(tr_one.xpath('./td'),tr_two.xpath('./td')):
            key = get_alltext(td_one).strip()
            value = get_alltext(td_two).strip()
            if key and value:
                result[key] = value
    return result



















