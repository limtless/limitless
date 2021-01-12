from regular_matching_rules import get_keywordTredTree_instance
from spidertools.utils.snippets import combine_two_dict
from configs.commom import mode_to_table, list_key, DBTableInfo
import copy
from info_fsm_utils import get_triedtree_result, clean_triedtree_keys, conbine_contract_and_agent_mode


class BaseBidState():
    def __init__(self, mode):
        self.mode = mode
        self.db_key = mode_to_table[mode]
        self.info_dict = {}
        self.info_dict[DBTableInfo.PROJECT] = {}
        self.info_dict[DBTableInfo.PROJECT_ANNOUNCEMENT] = {}
        self.info_dict[DBTableInfo.PROJECT_BID_INFORMATION] = {}
        self.info_dict[DBTableInfo.PROJECT_WIN_BIDDING_INFORMATION] = {}
        self.info_dict[DBTableInfo.UNKNOW] = {}
        self.info_dict[DBTableInfo.IGNORE] = {}


    def reset_state(self):
        '''重置State'''
        self.info_dict = {}
        self.info_dict[DBTableInfo.PROJECT] = {}
        self.info_dict[DBTableInfo.PROJECT_ANNOUNCEMENT] = {}
        self.info_dict[DBTableInfo.PROJECT_BID_INFORMATION] = {}
        self.info_dict[DBTableInfo.UNKNOW] = {}
        self.info_dict[DBTableInfo.PROJECT_WIN_BIDDING_INFORMATION] = {}
        self.info_dict[DBTableInfo.IGNORE] = {}

    def check_key(self,key):
        if key in list_key:
            return True
        else:
            return False

    def output_result(self):
        result = copy.deepcopy(self.info_dict)
        self.reset_state()
        return result

    def update_state_info(self, item):
        '''
        根据传入的item信息跟新当前State里面的dict
        :param item:
        :return:
        '''
        if item["explicit_type"]:
            for key, value in item["explicit_type"].items():
                table, table_key = key.split("-")
                if self.check_key(table_key):
                    if table_key not in self.info_dict[table]:
                        self.info_dict[table][table_key] = [value]
                    else:
                        if value not in self.info_dict[table][table_key]:
                            self.info_dict[table][table_key].append(value)
                else:
                    self.info_dict[table][table_key] = value


        if item['common_type']:
            for key, value in item['common_type'].items():
                if self.check_key(self.mode + key):
                    if self.mode + key not in self.info_dict[self.db_key]:
                        self.info_dict[self.db_key][self.mode + key] = [value]
                    else:
                        if value not in self.info_dict[self.db_key][self.mode + key]:
                            self.info_dict[self.db_key][self.mode + key].append(value)
                else:
                    self.info_dict[self.db_key][self.mode + key] = value






class BidAgencyState(BaseBidState):
    '''
    招标代理人信息提取状态
    '''

    def __init__(self):
        super(BidAgencyState, self).__init__(mode="招标代理机构")
        self.bidder_info = {}

    def reset_state(self):
        BaseBidState.reset_state(self)
        self.bidder_info = {}


class BidderState(BaseBidState):
    '''
    招标人信息提取状态
    '''

    def __init__(self):
        super(BidderState, self).__init__(mode="招标人信息")


class ProjectBaseInfoState(BaseBidState):
    '''
    工程基本信息提取状态
    '''

    def __init__(self):
        super(ProjectBaseInfoState, self).__init__(mode="工程基本信息")


class DealBidInfoState(BaseBidState):
    '''
    成交信息提取状态
    '''

    def __init__(self):
        super(DealBidInfoState, self).__init__(mode='中标信息')


class ProjectAnnouncementState(BaseBidState):
    '''
    工程公告状态
    '''

    def __init__(self):
        super(ProjectAnnouncementState, self).__init__(mode="工程公告信息")


class BidderAndAgentState(BaseBidState):
    '''
    未知状态
    '''

    def __init__(self):
        super(BidderAndAgentState, self).__init__(mode="招标人和招标代理机构")
        self.mode_list = ["招标人信息", '招标代理机构']
        self.visit_keys = {}

    def reset_state(self):
        BaseBidState.reset_state(self)
        self.visit_keys = {}

    def update_state_info(self, item):
        '''
        根据传入的item信息跟新当前State里面的dict
        :param item:
        :return:
        '''
        if item["explicit_type"]:
            for key, value in item["explicit_type"].items():
                table, table_key = key.split("-")
                if self.check_key(table_key):
                    if table_key not in self.info_dict[table]:
                        self.info_dict[table][table_key] = [value]
                    else:
                        self.info_dict[table][table_key].append(value)
                else:
                    self.info_dict[table][table_key] = value

        if item['common_type']:
            for key, value in item['common_type'].items():

                if key not in self.visit_keys:
                    self.visit_keys[key] = 0
                else:
                    self.visit_keys[key] = (self.visit_keys[key] + 1) %2
                current_mode = self.mode_list[self.visit_keys[key]]

                if self.check_key(current_mode + key):
                    if current_mode + key not in self.info_dict[self.db_key]:
                        self.info_dict[self.db_key][current_mode + key] = [value]
                    else:
                        if value not in self.info_dict[self.db_key][current_mode + key]:
                            self.info_dict[self.db_key][current_mode + key].append(value)
                else:
                    self.info_dict[self.db_key][current_mode + key] = value

        #convert_valuelist_to_str(self.info_dict, list_key)


class StartState(BaseBidState):
    '''
    未知状态
    '''

    def __init__(self):
        super(StartState, self).__init__(mode="未知")

class IgnoreState(BaseBidState):
    '''
    忽略状态
    '''

    def __init__(self):
        super(IgnoreState, self).__init__(mode="忽略")

    def output_result(self):
        result = copy.deepcopy(self.info_dict)
        self.reset_state()
        return result

    def update_state_info(self, item):
        '''
        根据传入的item信息跟新当前State里面的dict
        :param item:
        :return:
        '''
        if item["explicit_type"]:
            for key, value in item["explicit_type"].items():
                table, table_key = key.split("-")
                if self.check_key(table_key):
                    if table_key not in self.info_dict[table]:
                        self.info_dict[table][table_key] = [value]
                    else:
                        if value not in self.info_dict[table][table_key]:
                            self.info_dict[table][table_key].append(value)
                else:
                    self.info_dict[table][table_key] = value




class InfoMachine(object):
    def __init__(self, base_regex=None,extend_keywords=None):

        self.base_regex = base_regex
        self.triedTree = get_keywordTredTree_instance()

        if extend_keywords:
            self.triedTree = copy.deepcopy(self.triedTree)
            self.triedTree.update_triedTree_keys(extend_keywords)

        self.states = {
            "未知": StartState(),
            "招标代理机构": BidAgencyState(),
            '招标人信息': BidderState(),
            "工程基本信息": ProjectBaseInfoState(),
            "工程公告信息": ProjectAnnouncementState(),
            "中标信息": DealBidInfoState(),
            "招标人和招标代理人信息": BidderAndAgentState(),
            "忽略": IgnoreState(),
        }
        self.current_state_str = "未知"
        self.current_state = self.states[self.current_state_str]

    def run_list(self, text_list):
        text_dict_list = []
        for text in text_list:
            text = clean_triedtree_keys(text)  # 去除关键字之间的NBSP/空格等，其他的NBSP未处理，加上关键字冒号的形式
            item = get_triedtree_result(text, self.base_regex)
            if item:
                text_dict_list.extend(item)

        conbine_contract_and_agent_mode(text_dict_list)

        result = {}
        for index, text in enumerate(text_dict_list):
            output = self.exec(text)
            if output != None and output != {}:
                result = combine_two_dict(result, output)

        output = self.current_state.output_result()
        result = combine_two_dict(result, output)

        for key in list(result.keys()):
            if not result[key]:
                del result[key]

        return result

    def update_state(self, new_state):
        output = {}
        if new_state and self.current_state_str != new_state:
            output = self.current_state.output_result()
            self.current_state = self.states[new_state]
            self.current_state_str = new_state
        return output

    def exec(self, item):
        if item:
            output = self.update_state(item["mode"])
            self.current_state.update_state_info(item)
        else:
            output = {}
        return output
