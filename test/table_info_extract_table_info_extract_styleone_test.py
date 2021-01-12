from table_info_extract.extract_utils import table_info_extract_styleone
from bs4 import BeautifulSoup
from scrapy.selector import Selector
from pprint import pprint


if __name__ == '__main__':
    html_str = """

<html>
    <body>
        <table cellpadding="0" cellspacing="0" class="D_tableBox">
           <tbody><tr>
              <th width="15%">地区</th>
              <td width="35%">苏州</td>
              <th width="15%">类别</th>
              <td width="35%">工程类</td>
           </tr>
           <tr>
              <th>采购方式</th>
              <td>竞争性磋商招标</td>
              <th>项目名称</th>
              <td>教学楼及艺体楼屋面防水、体育场司令台等维修改造</td>
           </tr>
           <tr>
              <th>采购单位</th>
              <td>苏州市第十二中学校</td>
              <th>代理机构</th>
              <td>苏州玮源招投标咨询服务有限公司</td>
           </tr>
           <tr>
              <th>项目预算</th>
              <td>852348.20元</td>
              <th>公示时间</th>
              <td>2020-06-28 16:41:42</td>
           </tr>
        </tbody>
        </table>
    </body>
</html>
"""

    sel = Selector(text=html_str)
    table_node = sel.xpath("//table[@class='D_tableBox']")[0]
    pprint(table_info_extract_styleone(table_node))