# -*- coding: utf-8 -*- 
# @Time : 2020/12/4 9:29 
# @Author : limpo 
# @File : checkjson.py 
# @desc:


def checkexojson(doc):
    '''
    1. 
    :param doc:
    :return:
    '''
    lock=[]
    secondkeys={'工程公告信息':['工程公告信息发布时间','公告标题'],'工程基本信息':['项目名称'],'工程投标信息':['中标信息名称']}
    firstkeys=list(secondkeys.keys())
    basekeys=doc.keys()
    # basekeys=['_id', '工程基本信息', '工程招标信息','工程公告信息', '工程投标信息', '原始地址', '公告公告类型', '工程公告信息发布时间', 'search_key', 'is_parsed', 'create_time', 'update_time']
    diff=[j for j in firstkeys if j in basekeys]
    fflag=set(diff) == set(firstkeys)
    if fflag:
        pass
    else:
        lack_not_infirstkeys = [j for j in firstkeys if j not in diff]
        print('firstkeys lock:',lack_not_infirstkeys)
        lock.append(''.join(lack_not_infirstkeys))
    for dif in diff:
        real_secondkeys=list(doc[dif].keys())
        standard_secondkeys=secondkeys[dif]

        sediff = [j for j in real_secondkeys if j in standard_secondkeys]
        sflag=set(sediff) == set(standard_secondkeys)
        if sflag:
            pass
        else:
            lack_not_insecondkeys = [j for j in standard_secondkeys if j not in sediff]
            print('secondkeys lock:', {dif:lack_not_insecondkeys})
            lock.append(''.join(lack_not_insecondkeys))
    return lock
def checkjson(doc):
    secondkeyslist=[]
    firstkeyslist=[]
    secondkeys={"工程公告信息":['工程公告信息发布时间','公告标题'],"工程基本信息":['项目名称'],"工程投标信息":['中标信息名称']}
    for k ,v in secondkeys.items():
        secondkeyslist.extend(v)
        firstkeyslist.append(k)
    alllist=[]
    alllist.extend(secondkeyslist)
    alllist.extend(firstkeyslist)

    allreallist=[]
    realfirstlist=[]
    realsecondkeyslist=[]
    for k,v in doc.items():
        if type(v)==dict:
            realfirstlist.append(k)
            realsecondkeyslist.extend(list(v.keys()))
    allreallist.extend(realfirstlist)
    allreallist.extend(realsecondkeyslist)

    #如果有flag,没有‘项目名称’,true
    if "flag" in realsecondkeyslist:
        alllist.remove("项目名称")
        diff = [i for i in alllist if i in allreallist]
        blackpink = (diff == alllist)
    else:
        diff = [i for i in alllist if i in allreallist]
        blackpink = (diff == alllist)
    return blackpink


if __name__ == '__main__':
    doc = [{
    "工程基本信息" : {
        "项目编号" : "JITC-2001AH2634二、",
        # "项目名称" : "南京信息职业技术学院概念设计实训室设备项目三、",
        "flag": "PROJECT_NAME_FROM_BID_SECTION_NUM",
    },
    "工程招标信息" : {
        "招标人信息名称" : [
            "南京信息职业技术学院",
            "江苏省招标中心有限公司"
        ],
        "招标人信息地址" : [
            "南京市栖霞区文澜路99号",
            "江苏省南京市西康路7号"
        ],
        "招标人信息电话" : [
            "韦老师　025-85842494   2."
        ],
        "招标代理机构电话" : [
            "黄沛、李欣阳、傅承　025-83249912　3.",
            "025-83633702  联系邮箱:jszfcgbx@163.com      "
        ],
        "招标人信息联系人" : [
            "黄沛、李欣阳、傅承电　话:　025-83249912　　十、附件1.采购文件2.报价单江苏省招标中心有限公司2020年11月11日  附件:概念设计实训室设备采购文件.doc南京茂立报价单.pdf"
        ]
    },
    "工程投标信息" : {
        "中标信息名称" : "详见附件品牌(如有):详见附件规格型号:详见附件数量:详见附件单价:详见附件五、评审专家名单:戴雪头、张  婷、王利雅、邓开明、邵向前(采购人代表)六、代理服务收费标准及金额:参照原计价格(2002)1980号文中的货物类标准70%计取,中标服务费由中标人支付,收费金额:人民币0.7278万元七、公告期限自本公告发布之日起1个工作日。八、其他补充事宜各有关当事人对中标公告结果有异议的,可以在中标公告期限届满之日起七个工作日内,以书面原件形式提出明确的请求并提供必要的证明材料,向江苏省招标中心有限公司提出质疑,逾期将不再受理。九、凡对本次公告内容提出询问,请按以下方式联系。1.",
        "中标信息地址" : "南京市玄武区珠江路435号1107室",
        "中标金额" : "人民币69.316万元四、"
    },
    "工程公告信息" : {
        "公告标题" : "南京信息职业技术学院概念设计实训室设备项目中标结果公告",
        "工程公告信息发布时间" : "2020-11-11",
        "公告类型" : "中标公告",
    },
    "原始地址" : "http://www.ccgp-jiangsu.gov.cn/ggxx/zgysgg/../zbgg/./shengji/./202011/t20201111_750899.html",
    "公告公告类型" : "中标公告",
    "工程公告信息发布时间" : "2020-11-11",
    "search_key" : "http://www.ccgp-jiangsu.gov.cn/ggxx/zgysgg/../zbgg/./shengji/./202011/t20201111_750899.html$$中标公告$$2020-11-11",
    "is_parsed" : 1,
    "create_time" : "2020-12-02 18:15:03",
    "update_time" : "2020-12-02 18:15:03"
}]
    for i in doc:
        print(checkjson(i))
