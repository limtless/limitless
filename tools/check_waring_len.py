# -*- coding:utf-8 -*-

def check_len(path,times=0):  #path为log文档的绝对地址，记得加r。times是要显示测试信息的条数,不输入则全显示
    from pprint import pprint
    import re
    import random
    f = open(path, "r", encoding='utf-8')
    lines = f.readlines()  # 读取全部内容 ，并以列表方式返回
    wrong_dic = {}
    i=1
    for line in lines:
        wrong = re.findall(r"#(.*?)#[{]", line)[0]
        #print(wrong)
        wrong = '#' + wrong + '#'
        wrong_type_list = re.findall(r"#(.*?):", wrong)
        wrong_title = re.findall(r'"公告标题": (.*?),',line)[0]
        second_list = [0, []]
        # i+=1
        # print(i)
        # print(wrong_type_list)
        if '跳转前网页' in line:
            wrong_url = re.findall(r'"跳转前网页": (.*?),', line)[0]
        else:
            wrong_url = re.findall(r'"origin_url": (.*?),', line)[0]
        small_dic = {wrong_title: wrong_url}
        for wrong_type in wrong_type_list:
            if wrong_type in wrong_dic.keys():
                wrong_dic[wrong_type][0] += 1
                wrong_dic[wrong_type][1].append(small_dic)
            else:
                second_list[0]=i
                second_list[1].append(small_dic)
                wrong_dic.update({wrong_type:second_list})
    for wrong_type in wrong_dic.keys():
        if times ==0:
            pass
        elif len(wrong_dic[wrong_type][1]) > 6:
            i=0
            test_list =[]
            while i < times:
                i+=1
                test_list.append(random.choice(wrong_dic[wrong_type][1]))
            wrong_dic[wrong_type][1] = test_list

    pprint(wrong_dic)


if __name__ == '__main__':
    #path = r'D:\迅雷下载\company_info_extrator\log_files\2021-01-08\Waring_ContentLenMoreThan100.log'
    #path = r'D:\work\company_info_extrator\log_files\2021-01-11\Waring_WeiZhiKeyWords.log'
    path = r'D:\work\company_info_extrator\log_files\2021-01-11\Waring_ContentLenMoreThan100.log'
    times = 6
    check_len(path,times)#path为log文档的绝对地址，记得加r。times是要显示测试信息的条数,不输入则全显示
