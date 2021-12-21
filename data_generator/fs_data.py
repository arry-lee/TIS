# 利润表 负债表 现金流量表 权益变动表

# 数据自然是爬虫获取的
# 所需做的是展示数据的视图

# 1. 一个公司，时间 一

from enum import Enum
from awesometable import AwesomeTable
import pandas as pd

from awesometable import table2image
from utils.cv_tools import cvshow

class Statement:
    def __init__(self,company,date):
        self.company = company
        self.date = date
        self.header = []
        self.body = []

    def bulid_table(self):
        pass

class FinancialPositionStatement(Statement):
    name = '资产负债表'
    desc = """资产负债表一般有表首、正表两部分。
        其中，表首概括地说明报表名称、编制单位、编制日期、报表编号、货币名称、计量单位等。
        正表是资产负债表的主体，列示了用以说明企业财务状况的各个项目。
        资产负债表正表的格式一般有两种：报告式资产负债表和账户式资产负债表。
        报告式资产负债表是上下结构，上半部列示资产，下半部列示负债所有者权益
        具体排列形式又有两种：一是按“资产=负债+所有者权益”的原理排列；
        二是按“资产-负债=所有者权益”的原理排列。
        账户式资产负债表是左右结构，左边列示资产，右边列示负债和所有者权益。
        不管采取什么格式，资产各项目的合计等于负债和所有者权益各项目的合计这一等式不变。
        """
    header_string = """<table style="width: 100%">
                    <caption> <b>资产负债表</b>
                    </caption>
                    <tbody><tr>
                    <td colspan="3" style="text-align:right;">会企01表
                    </td></tr>
                    <tr>
                    <td style="width: 30%"> 编制单位：××有限公司
                    </td><td style="width: 40%; text-align: center;"> 20×8年12月31日
                    </td><td style="width: 30%; text-align: right;"> 单位：元
                    </td></tr></tbody></table>"""

    body_string = """<table class="wikitable" style="width:100%; font-size: 100%;">
<tbody><tr>
<th>资　　产</th><th>期末余额</th><th>年初余额
</th><th>负债和所有者权益<br>（或股东权益）</th><th>期末余额</th><th>年初余额
</th></tr>
<tr>
<td><a href="/wiki/%E6%B5%81%E5%8A%A8%E8%B5%84%E4%BA%A7" title="流动资产">流动资产</a>：</td><td></td><td>
</td><td><a href="/wiki/%E6%B5%81%E5%8A%A8%E8%B4%9F%E5%80%BA" title="流动负债">流动负债</a>：</td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E8%B4%A7%E5%B8%81%E8%B5%84%E9%87%91" title="货币资金">货币资金</a></td><td></td><td>
</td><td>　<a href="/wiki/%E7%9F%AD%E6%9C%9F%E5%80%9F%E6%AC%BE" title="短期借款">短期借款</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E4%BA%A4%E6%98%93%E6%80%A7%E9%87%91%E8%9E%8D%E8%B5%84%E4%BA%A7" title="交易性金融资产">交易性金融资产</a></td><td></td><td>
</td><td>　<a href="/wiki/%E4%BA%A4%E6%98%93%E6%80%A7%E9%87%91%E8%9E%8D%E8%B4%9F%E5%80%BA" title="交易性金融负债">交易性金融负债</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%BA%94%E6%94%B6%E7%A5%A8%E6%8D%AE" title="应收票据">应收票据</a></td><td></td><td>
</td><td>　<a href="/wiki/%E5%BA%94%E4%BB%98%E7%A5%A8%E6%8D%AE" title="应付票据">应付票据</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%BA%94%E6%94%B6%E8%B4%A6%E6%AC%BE" title="应收账款">应收账款</a></td><td></td><td>
</td><td>　<a href="/wiki/%E5%BA%94%E4%BB%98%E8%B4%A6%E6%AC%BE" title="应付账款">应付账款</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E9%A2%84%E4%BB%98%E6%AC%BE%E9%A1%B9" title="预付款项">预付款项</a></td><td></td><td>
</td><td>　<a href="/wiki/%E9%A2%84%E6%94%B6%E6%AC%BE%E9%A1%B9" title="预收款项">预收款项</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%BA%94%E6%94%B6%E5%88%A9%E6%81%AF" title="应收利息">应收利息</a></td><td></td><td>
</td><td>　<a href="/wiki/%E5%BA%94%E4%BB%98%E8%81%8C%E5%B7%A5%E8%96%AA%E9%85%AC" title="应付职工薪酬">应付职工薪酬</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%BA%94%E6%94%B6%E8%82%A1%E5%88%A9" title="应收股利">应收股利</a></td><td></td><td>
</td><td>　<a href="/wiki/%E5%BA%94%E4%BA%A4%E7%A8%8E%E8%B4%B9" title="应交税费">应交税费</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%85%B6%E4%BB%96%E5%BA%94%E6%94%B6%E6%AC%BE" title="其他应收款">其他应收款</a></td><td></td><td>
</td><td>　<a href="/wiki/%E5%BA%94%E4%BB%98%E5%88%A9%E6%81%AF" title="应付利息">应付利息</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%AD%98%E8%B4%A7" title="存货">存货</a></td><td></td><td>
</td><td>　<a href="/wiki/%E5%BA%94%E4%BB%98%E8%82%A1%E5%88%A9" title="应付股利">应付股利</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E4%B8%80%E5%B9%B4%E5%86%85%E5%88%B0%E6%9C%9F%E7%9A%84%E9%9D%9E%E6%B5%81%E5%8A%A8%E8%B5%84%E4%BA%A7" title="一年内到期的非流动资产">一年内到期的非流动资产</a></td><td></td><td>
</td><td>　<a href="/wiki/%E5%85%B6%E4%BB%96%E5%BA%94%E4%BB%98%E6%AC%BE" title="其他应付款">其他应付款</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%85%B6%E4%BB%96%E6%B5%81%E5%8A%A8%E8%B5%84%E4%BA%A7" title="其他流动资产">其他流动资产</a></td><td></td><td>
</td><td>　<a href="/wiki/%E4%B8%80%E5%B9%B4%E5%86%85%E5%88%B0%E6%9C%9F%E7%9A%84%E9%9D%9E%E6%B5%81%E5%8A%A8%E8%B4%9F%E5%80%BA" title="一年内到期的非流动负债">一年内到期的非流动负债</a></td><td></td><td>
</td></tr>
<tr>
<td style="text-align:center;"><b><a href="/wiki/%E6%B5%81%E5%8A%A8%E8%B5%84%E4%BA%A7%E5%90%88%E8%AE%A1" title="流动资产合计">流动资产合计</a></b></td><td></td><td>
</td><td>　<a href="/wiki/%E5%85%B6%E4%BB%96%E6%B5%81%E5%8A%A8%E8%B4%9F%E5%80%BA" title="其他流动负债">其他流动负债</a></td><td></td><td>
</td></tr>
<tr>
<td><a href="/wiki/%E9%9D%9E%E6%B5%81%E5%8A%A8%E8%B5%84%E4%BA%A7" title="非流动资产">非流动资产</a>：</td><td></td><td>
</td><td style="text-align:center;"><b><a href="/wiki/%E6%B5%81%E5%8A%A8%E8%B4%9F%E5%80%BA%E5%90%88%E8%AE%A1" title="流动负债合计">流动负债合计</a></b></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%8F%AF%E4%BE%9B%E5%87%BA%E5%94%AE%E9%87%91%E8%9E%8D%E8%B5%84%E4%BA%A7" title="可供出售金融资产">可供出售金融资产</a></td><td></td><td>
</td><td><a href="/wiki/%E9%9D%9E%E6%B5%81%E5%8A%A8%E8%B4%9F%E5%80%BA" title="非流动负债">非流动负债</a>：</td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E6%8C%81%E6%9C%89%E8%87%B3%E5%88%B0%E6%9C%9F%E6%8A%95%E8%B5%84" title="持有至到期投资">持有至到期投资</a></td><td></td><td>
</td><td>　<a href="/wiki/%E9%95%BF%E6%9C%9F%E5%80%9F%E6%AC%BE" title="长期借款">长期借款</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E9%95%BF%E6%9C%9F%E5%BA%94%E6%94%B6%E6%AC%BE" title="长期应收款">长期应收款</a></td><td></td><td>
</td><td>　<a href="/wiki/%E5%BA%94%E4%BB%98%E5%80%BA%E5%88%B8" title="应付债券">应付债券</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E9%95%BF%E6%9C%9F%E8%82%A1%E6%9D%83%E6%8A%95%E8%B5%84" title="长期股权投资">长期股权投资</a></td><td></td><td>
</td><td>　<a href="/wiki/%E9%95%BF%E6%9C%9F%E5%BA%94%E4%BB%98%E6%AC%BE" title="长期应付款">长期应付款</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E6%8A%95%E8%B5%84%E6%80%A7%E6%88%BF%E5%9C%B0%E4%BA%A7" title="投资性房地产">投资性房地产</a></td><td></td><td>
</td><td>　<a href="/wiki/%E4%B8%93%E9%A1%B9%E5%BA%94%E4%BB%98%E6%AC%BE" title="专项应付款">专项应付款</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%9B%BA%E5%AE%9A%E8%B5%84%E4%BA%A7" title="固定资产">固定资产</a></td><td></td><td>
</td><td>　<a href="/wiki/%E9%A2%84%E8%AE%A1%E8%B4%9F%E5%80%BA" title="预计负债">预计负债</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%9C%A8%E5%BB%BA%E5%B7%A5%E7%A8%8B" title="在建工程">在建工程</a></td><td></td><td>
</td><td>　<a href="/wiki/%E9%80%92%E5%BB%B6%E6%89%80%E5%BE%97%E7%A8%8E%E8%B4%9F%E5%80%BA" title="递延所得税负债">递延所得税负债</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%B7%A5%E7%A8%8B%E7%89%A9%E8%B5%84" title="工程物资">工程物资</a></td><td></td><td>
</td><td>　<a href="/wiki/%E5%85%B6%E4%BB%96%E9%9D%9E%E6%B5%81%E5%8A%A8%E8%B4%9F%E5%80%BA" title="其他非流动负债">其他非流动负债</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%9B%BA%E5%AE%9A%E8%B5%84%E4%BA%A7%E6%B8%85%E7%90%86" title="固定资产清理">固定资产清理</a></td><td></td><td>
</td><td style="text-align:center;"><b>非流动负债合计</b></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E7%94%9F%E4%BA%A7%E6%80%A7%E7%94%9F%E7%89%A9%E8%B5%84%E4%BA%A7" title="生产性生物资产">生产性生物资产</a></td><td></td><td>
</td><td style="text-align:center;"><b><a href="/wiki/%E8%B4%9F%E5%80%BA%E5%90%88%E8%AE%A1" title="负债合计">负债合计</a></b></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E6%B2%B9%E6%B0%94%E8%B5%84%E4%BA%A7" title="油气资产">油气资产</a></td><td></td><td>
</td><td><a href="/wiki/%E6%89%80%E6%9C%89%E8%80%85%E6%9D%83%E7%9B%8A" title="所有者权益">所有者权益</a>（或<a href="/wiki/%E8%82%A1%E4%B8%9C%E6%9D%83%E7%9B%8A" title="股东权益">股东权益</a>）：</td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E6%97%A0%E5%BD%A2%E8%B5%84%E4%BA%A7" title="无形资产">无形资产</a></td><td></td><td>
</td><td>　<a href="/wiki/%E5%AE%9E%E6%94%B6%E8%B5%84%E6%9C%AC" title="实收资本">实收资本</a>（或<a href="/wiki/%E8%82%A1%E6%9C%AC" title="股本">股本</a>）</td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%BC%80%E5%8F%91%E6%94%AF%E5%87%BA" title="开发支出">开发支出</a></td><td></td><td>
</td><td>　<a href="/wiki/%E8%B5%84%E6%9C%AC%E5%85%AC%E7%A7%AF" title="资本公积">资本公积</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%95%86%E8%AA%89" title="商誉">商誉</a></td><td></td><td>
</td><td>　减：<a href="/wiki/%E5%BA%93%E5%AD%98%E8%82%A1" title="库存股">库存股</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E9%95%BF%E6%9C%9F%E5%BE%85%E6%91%8A%E8%B4%B9%E7%94%A8" title="长期待摊费用">长期待摊费用</a></td><td></td><td>
</td><td>　<a href="/wiki/%E7%9B%88%E4%BD%99%E5%85%AC%E7%A7%AF" title="盈余公积">盈余公积</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E9%80%92%E5%BB%B6%E6%89%80%E5%BE%97%E7%A8%8E%E8%B5%84%E4%BA%A7" title="递延所得税资产">递延所得税资产</a></td><td></td><td>
</td><td>　<a href="/wiki/%E6%9C%AA%E5%88%86%E9%85%8D%E5%88%A9%E6%B6%A6" title="未分配利润">未分配利润</a></td><td></td><td>
</td></tr>
<tr>
<td>　<a href="/wiki/%E5%85%B6%E4%BB%96%E9%9D%9E%E6%B5%81%E5%8A%A8%E8%B5%84%E4%BA%A7" title="其他非流动资产">其他非流动资产</a></td><td></td><td>
</td><td style="text-align:center;"><b><a href="/wiki/%E6%89%80%E6%9C%89%E8%80%85%E6%9D%83%E7%9B%8A" title="所有者权益">所有者权益</a>（或<a href="/wiki/%E8%82%A1%E4%B8%9C%E6%9D%83%E7%9B%8A" title="股东权益">股东权益</a>）合计</b></td><td></td><td>
</td></tr>
<tr>
<td style="text-align:center;"><b>非流动资产合计</b></td><td></td><td>
</td><td></td><td></td><td>
</td></tr>
<tr>
<td style="text-align:center;"><b><a href="/wiki/%E8%B5%84%E4%BA%A7%E6%80%BB%E8%AE%A1" title="资产总计">资产总计</a></b></td><td></td><td>
</td><td style="text-align:center;"><b>负债和所有者权益（或股东权益）总计</b></td><td></td><td>
</td></tr></tbody></table>"""

    def __init__(self,company,date,header=None,body=None):
        Statement.__init__(self,company,date)
        self.header =[ ['','','','','','会企01表'],
                    ['编制单位：',self.company,'',self.date,'','单位：元']]

        self.body = pd.read_html(self.body_string)[0]
        # self.header = from_list(self.header)
        # self.body = from_dataframe(self.body)
        self.bulid_table()
        self.get_keys()

    def get_keys(self):
        df = self.body
        keys = df['资 产']
        print(keys)

    def bulid_table(self):
        self.table = AwesomeTable()
        self.table.add_rows(self.header)
        self.table.add_row(list(self.body.columns))
        self.table.add_rows([row.tolist() for row in self.body.values])
        self.table.title = self.name
        self.table.align = 'l'

    def show(self):
        print(self.table)

        img = table2image(self.table)['image']
        cvshow(img)

a = FinancialPositionStatement(company='xx公司',date='2021年12月16日')
a.show()

class FSType(Enum):
    LIRY = 1
    FUVD = 2
    XMJK = 3
    QRYI = 4



# 输入一个公司或股票代码，输出一套财务数据
class FSDataGenerator(object):
    def __init__(self,company_code):
        pass

    def get_data(self):
        return

    def __call__(self, *args, **kwargs):
        pass


