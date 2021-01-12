from spidertools.utils.tried_tree_utils import InfoTriedTree

from project_setting import KEYWORDS_DATA_PATH

global_dict = {}


def get_keywordTredTree_instance():
    if 'keyword' not in global_dict:
        global_dict["keyword"] = InfoTriedTree(KEYWORDS_DATA_PATH)  # KEYWORDS_DATA_PATH就是对应的字典的路径

    return global_dict['keyword']


if __name__ == '__main__':
    print(get_keywordTredTree_instance().get_word_types("名称"))