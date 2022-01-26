import random
from math import ceil

import numpy as np
import pandas as pd
import prettytable
from faker import Faker
from mimesis.schema import Field, Schema
from prettytable import PrettyTable, FRAME

from awesometable import vstack, AwesomeTable
from .fakekeys import key_value_generator
from static.logo import bank_list

# label_dir = ''
# keys_dict, values_dict, texts, keys, values = key_value_generator(label_dir)

# def _random_long_sentence():
#     return random.choice(texts)

f = Faker('zh_CN')
_ = Field('zh')


def _rmb_upper(value):
    """
    人民币大写
    传入浮点类型的值返回 unicode 字符串
    """
    map = [u"零", u"壹", u"贰", u"叁", u"肆", u"伍", u"陆", u"柒", u"捌", u"玖"]
    unit = [u"分", u"角", u"元", u"拾", u"百", u"千", u"万", u"拾", u"百", u"千",
            u"亿",
            u"拾", u"百", u"千", u"万", u"拾", u"百", u"千", u"兆"]

    nums = []  # 取出每一位数字，整数用字符方式转换避大数出现误差
    for i in range(len(unit) - 3, -3, -1):
        if value >= 10 ** i or i < 1:
            nums.append(int(round(value / (10 ** i), 2)) % 10)

    words = []
    zflag = 0  # 标记连续0次数，以删除万字，或适时插入零字
    start = len(nums) - 3
    for i in range(start, -3, -1):  # 使i对应实际位数，负数为角分
        if 0 != nums[start - i] or len(words) == 0:
            if zflag:
                words.append(map[0])
                zflag = 0
            words.append(map[nums[start - i]])
            words.append(unit[i + 2])
        elif 0 == i or (0 == i % 4 and zflag < 3):  # 控制‘万/元’
            words.append(unit[i + 2])
            zflag = 0
        else:
            zflag += 1

    if words[-1] != unit[0]:  # 结尾非‘分’补整字
        words.append(u"整")
    return ''.join(words)

field_dict = {
     '工作日期': ['日期', '交易日期', '交易时间', '入账日期', '记账日期', '交易日'],
     '账号': ['卡号', '主卡卡号', '账号/卡号', '借记卡卡号'],
     '注释': ['摘要', '交易摘要', '交易种类', '摘要代码', '交易名称', '交易描述', '备注'],
     '钞汇': ['现转'],
     '余额': ['账户余额', '交易余额', '账号余额', '联机余额', '活存账户余额'],
     '应用号': ['产品大类', '存款种类', '产品子类'],
     '网点号': ['网点', '交易网点'],
     '操作员': ['交易柜员', '柜员', '柜员流水号', '授权柜员号', '柜员号'],
     '地区号': ['交易地点'],
     '币种': ['货币'],
     '通知种类': ['发行代码'],
     '发生额': ['交易金额'],
     }


def _alias(key):
    return random.choice(field_dict[key]+[key])


class BankDetailProvider(object):
    """银行流水单据生成器"""
    _banks = bank_list
    def __init__(self):
        self.fk = Faker('zh_CN')

    def __call__(self, *args, **kwargs):
        self.name = self.fk.name()
        self.bank = random.choice(self._banks)
        self.cardnumber = self.fk.credit_card_number()
        self.start = self.fk.date_this_decade()
        self.money = random.randint(10000, 100000)
        nums = _('integer_number', start=10, end=20)

        self.df = pd.DataFrame({
            '工作日期': pd.date_range(self.start, periods=nums, freq='M').strftime(
                '%Y-%m-%d'),
            '账号': self.cardnumber,
            '应用号': 1,
            '序号': range(1, nums + 1),
            '币种': 'RMB',
            '钞汇': '钞',
            '交易代码': np.random.randint(0, 3, nums),
            '注释': np.random.choice(['工资', 'ATM转账', 'ATM取款', '消费', '现存'], nums),
            '借贷': '借',
            '发生额': [_('float_number', start=-1000, end=1000, precision=2) for i
                    in range(nums)],
            '余额': 0,
            '存期': 0,
            '约转期': '不转存',
            '通知种类': 0,
            '利息': 0,
            '利息税': 0,
            '起息日': self.start,
            '止息日': '2099-12-31',
            '地区号': _('zip_code'),
            '网点号': np.random.randint(1000, 1100, nums),
            '操作员': np.random.randint(10000, 20000, nums),
            '界面': np.random.choice(['ATM交易', '网上银行', '批量业务', 'POS交易'], nums),
            # '多行文本':'这是一个很长很长很长很长很长很长很长很长很长很长很长很长的句子',
            # '摘要及明细': [_random_long_sentence() for i in range(nums)],

        })
        self.df['借贷'] = np.where(self.df['发生额'] > 0, '贷', '借')
        left = []
        for i in self.df['发生额']:
            lf = self.money + i
            left.append(lf)
            self.money = lf
        self.df['余额'] = pd.Series((round(i, 2) for i in left))
        self.df['发生额'] = np.abs(self.df['发生额'])


        return {'卡号': self.cardnumber,
                '户名': self.name,
                '银行': self.bank,
                '起始日期': str(self.start),
                '截止日期': self.df['工作日期'][nums - 1],
                '操作地区': self.df['地区号'][0],
                '操作网点': random.randint(1000, 1100),
                '操作柜员': random.randint(10000, 20000),
                '流水明细': self.df,
                }


bank_engine = BankDetailProvider()
bank_detail_generator = Schema(bank_engine)


def from_dataframe(df,max_cols=12,drop=True):
    """此处的方法太脏了，只能与banktable2image结合；耦合太严重了"""
    field_names = list(df.columns)
    if drop is True:
        dropkey = ['摘要及明细','应用号', '序号', '存期', '通知种类', '利息税', '操作员','界面','起息日','利息','约转期','地区号','止息日','钞汇','币种']
        for i in range(random.randint(0, len(dropkey))):
            field_names.remove(dropkey.pop())
    ndf = df.loc[:,field_names]
    # 更名
    for fno in range(len(field_names)):
        if field_names[fno] in field_dict.keys():
            field_names[fno] = _alias(field_names[fno])

    table = AwesomeTable()

    table.vrules = prettytable.ALL
    table.hrules = prettytable.ALL
    table.header = False
    table.set_style(15)

    max_cols = min(max_cols,random.randint(ceil(len(field_names)/2),len(field_names)//2*3)) # 太脏了

    if len(field_names) <= max_cols:
        table.add_row(field_names)
        for row in ndf.values:
            table.add_row(row.tolist())
        multi = False
    else:
        multi = True
        r = field_names
        table.add_row(r[:max_cols])
        table.add_row(r[max_cols:] + [' '] * (max_cols - len(r[max_cols:])))
        for rno,row in enumerate(ndf.values,start=1):
            r = row.tolist()
            table.add_row(r[:max_cols])
            table.add_row(r[max_cols:] + [' '] * (max_cols - len(r[max_cols:])))
    return table,multi


def bank_table_generator(bank_detail,max_width=16,align='l'):
    b = PrettyTable(header=False)
    b.set_style(15)
    b.vrules = FRAME

    b.title = bank_detail['银行'] + '账户历史明细清单'
    b.add_row(['卡号:' + bank_detail['卡号'],
               '户名:' + bank_detail['户名'],
               '起始日期:' + bank_detail['起始日期'],
               '截止日期:' + bank_detail['截止日期']
               ])
    c = PrettyTable(header=False)
    c.set_style(15)
    c.vrules = FRAME
    c.add_row(['操作地区:' + str(bank_detail['操作地区']),
               '操作网点:' + str(bank_detail['操作网点']),
               '操作柜员:' + str(bank_detail['操作柜员'])
               ])

    table,multi = from_dataframe(bank_detail['流水明细'])
    table.max_width = max_width
    table.align = align
    h = vstack([b, c, table])
    return h,multi


if __name__ == '__main__':
    t = bank_table_generator(bank_detail_generator.create(1)[0])
    print(t)
    from awesometable import banktable2image
    img = banktable2image(t,line_pad=-2)['image']
    from utils.cv_tools import cvshow
    cvshow(img)