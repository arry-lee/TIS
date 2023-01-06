"""
财报数据生成
"""
import random
import re
import sys
import textwrap
from collections import defaultdict
from itertools import cycle

import cv2
import faker
import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

sys.path.append("E:\\00IT\\P\\uniform")
from awesometable.awesometable import (
    AwesomeTable,
    H_SYMBOLS,
    count_padding,
    replace_chinese_to_dunder,
    str_block_width,
    paginate,
    V_LINE_PATTERN,
    vstack,
    wrap,
)
from awesometable.converter import from_list
from postprocessor.paper import Paper
from postprocessor.seal import add_seal_box, gen_name_seal, gen_seal
from utils.ulpb import encode

from awesometable.table2image import table2image


hit = lambda r: random.random() < r
_ = lambda x: x
CHINESE_NUM = "一二三四五六七八九十"
TRANS_DICT = {
    "项目": "ITEM",
    "本期发生额": "AMOUNT FOR THIS PERIOD",
    "上期发生额": "AMOUNT FOR LAST PERIOD",
    "本月实际": "ACTUAL AMOUNT THIS MONTH",
    "本年累计": "TOTAL AMOUNT THIS YEAR",
    "上年同期": "TOTAL AMOUNT LAST YEAR",
    "附注": "NOTES",
    "实收资本(或股本)": "PAID-IN OR SHARE CAPITAL",
    "资本公积": "CAPITAL RESERVE",
    "其他综合收益": "OTHER INCOME",
    "盈余公积": "SURPLUS RESERVE",
    "一般风险准备": "GENERAL RISK PREPARATION",
    "组合一": "GROUP ONE",
    "组合二": "GROUP TWO",
    "组合三": "GROUP THREE",
    "组合四": "GROUP FOUR",
    "组合五": "GROUP FIVE",
    "组合六": "GROUP SIX",
    "行次": "No.",
    "其他": "Other",
}
words = []
with open(r"E:\00IT\P\uniform\static\index.txt", encoding="utf-8") as f:
    for s in f.read().split():
        if len(s) > 30:
            words.append(s)
            
from faker import Faker
FAKE_CN = Faker('zh_CN')
random_words = lambda: FAKE_CN.word()


class FinancialStatementTable(object):
    """财报统一生成接口"""

    def __init__(self, name, lang="zh_CN", random_price=None):
        self.faker = faker.Faker(lang)
        self.is_zh = "zh" in lang
        if random_price:
            self.random_price = random_price
        else:
            self.random_price = lambda: "{:,}".format(random.randint(100000, 10000000))

        if self.is_zh:
            config_path = "./financial_statement/config/fs_config_zh.yaml"
        else:
            config_path = "./financial_statement/config/fs_config_en.yaml"
            ## 翻译组件
            def trans(chr):
                if chr in TRANS_DICT.keys():
                    return "\n".join(TRANS_DICT[chr].split())
                return encode(chr).upper()

            global _
            _ = trans

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)

        self.name = name
        self.index = self.config[name]

        self._columns_list = [
            [_("项目"), _("本期发生额"), _("上期发生额")],
            [_("项目"), _("本月实际"), _("本年累计"), _("上年同期")],
            [_("项目"), _("其他"), _("本月实际"), _("本年累计"), _("上年同期")],
            [_("项目"), _("实收资本(或股本)"), _("资本公积"), _("其他综合收益"), _("盈余公积")],
            [_("项目"), _("实收资本(或股本)"), _("资本公积"), _("其他综合收益"), _("盈余公积"), _("一般风险准备")],
        ]
        self._columns_generator = cycle(self._columns_list)
        self._table_width = None

    def ops_dispatch(self):
        """
        # 对于生成的表格根据其长度分发到不同的操作
        # cols <= 3 分割重组 hstack
        # cols > 5  复杂表头
        # rows > max_perpage 截断或分页
        # rows < half_max_perpage vstack 多表
        """
        c = len(self._columns)
        r = sum(len(v) + 1 for v in self.index.values() if v)
        rmax = 30  # 单页最大行数
        rmin = 15  # 低于此行数实行多表堆叠
        cmin = 3  # 低于此列数可以合并
        cmax = 6  # 大于此列复杂化

        if self.is_zh:
            self.can_hstack = hit(0.5) and r > rmax
            self.can_vstack = hit(0.5) and r > rmin
            self.can_paginate = r >= rmax and cmin < c < cmax
            self.can_truncate = True
            self.can_complex = hit(0.5) and c >= cmin
        else:
            self.can_hstack = hit(0.5)
            self.can_vstack = hit(0) and r > rmin
            self.can_paginate = r >= rmax and cmin < c < cmax
            self.can_truncate = True
            self.can_complex = hit(0.9) and c >= cmin

    def _base_info(self):
        self.company = self.faker.company()
        self.this_year = self.faker.date()
        self.last_year = str(int(self.this_year[:4]) - 1) + self.this_year[4:]
        if not self.is_zh:
            self._columns_list.pop()
        self._columns_list.append([_("项目"), self.this_year, self.last_year])
        self._columns = random.choice(
            self._columns_list
        )  # next(self._columns_generator)  #
        self._cpx_headers = (
            self.this_year,
            self.last_year,
            _("组合一"),
            _("组合二"),
            _("组合三"),
        )

        self._title = AwesomeTable()
        self._title.add_rows([[self.name], [self.this_year]])

        self._info = AwesomeTable()
        if self.is_zh:
            self._info.add_row(
                [_("编制单位:") + "%s" % self.company, _("单位：千元 币种：人民币 审计类型：未经审计")]
            )
        else:
            self._info.add_row(["  "])

    @property
    def columns(self):
        """列名"""
        return self._columns

    @property
    def title(self):
        """标题"""
        return self._title

    @property
    def info(self):
        """信息"""
        return self._info

    @property
    def footer(self, name_mark="〇"):
        """脚注"""
        _footer = AwesomeTable()
        if self.is_zh:
            _footer.add_row(
                [
                    _("公司负责人："),
                    self.faker.name() + name_mark,
                    _("主管会计工作负责人："),
                    self.faker.name() + name_mark,
                    _(" 会计机构负责人："),
                    self.faker.name() + name_mark,
                ]
            )
        else:
            _footer.add_row(
                [self.company.upper() + " Annual Report " + self.this_year[:4]]
            )
            _footer.align = "l"
        _footer.table_width = max(_footer.table_width, self.table_width)
        return _footer

    def metatable(self, **kwargs):
        """元表"""
        self._base_info()
        return self.build_table(**kwargs)

    @property
    def body(self):
        """主体"""
        return self.process_body(self.build_table())

    @property
    def table_width(self):
        """表宽"""
        return self._table_width or str(self.body).splitlines()[0].__len__()

    @table_width.setter
    def table_width(self, val):
        self._table_width = val

    def build_table(
        self,
        indent=2,
        fill_ratio=0.7,
        brace_ratio=0.3,
        auto_ratio=0.5,
        note_ratio=0.5,
        sign_ratio=0.5,
        title_ratio=0.3,
    ):
        """
        建立表格
        :param indent: int
        :param fill_ratio: float
        :param brace_ratio: float
        :param auto_ratio: float
        :param note_ratio: float
        :param sign_ratio: float
        :param title_ratio: float
        :return: str
        """
        t = AwesomeTable()
        columns = self._columns[:]
        if hit(auto_ratio):  # 控制行号的位置以及重复
            columns.insert(1, _("行次"))
        elif hit(note_ratio):
            columns.insert(2, _("附注"))
        elif hit(sign_ratio) and not self.is_zh:
            columns.insert(1, "$")

        t.add_row(columns)
        rno = 1
        for k, v in self.index.items():
            t.add_row([_(k).split()[0]] + [""] * (len(columns) - 1))
            if v is None:
                continue
            for item in v:
                if self.is_zh:
                    row = [self._indent_item(indent, item)]
                else:
                    row = [
                        item.split()[0].upper()
                        if hit(title_ratio)
                        else item.capitalize()
                    ]

                for c in columns[1:]:
                    if c == _("行次"):
                        row.append(rno)
                        rno += 1
                    elif c == "$":
                        row.append("$")

                    elif c == _("附注"):
                        if hit(fill_ratio):
                            row.append("({})".format(_(random.choice(CHINESE_NUM))))
                        else:
                            row.append(" ")
                    else:
                        if hit(fill_ratio):
                            if hit(brace_ratio):
                                row.append("({})".format(self.random_price()))
                            else:
                                row.append(self.random_price())
                        else:
                            row.append("-")

                t.add_row(row)
        return t

    @staticmethod
    def _indent_item(indent, item):
        if item[0] == "（":
            item = " " * indent * 2 + _(item)
        elif item[0].isdigit():
            item = " " * indent * 3 + _(item)
        else:
            item = " " * indent + _(item)
        return item

    def build_complex_header(self, table, cc=None):
        """
        增加复杂表头
        :param table: str|AwesomeTable
        :param cc:
        :return: str
        """
        lines = str(table).splitlines()
        # 移除表原来的表头
        for i in range(1, len(lines)):
            if lines[i][0] == "╠":
                break
        nt = lines[0] + "\n" + "\n".join(lines[i + 1 :])

        if not cc:
            if self.is_zh:
                cc = [c.strip() for c in re.split(V_LINE_PATTERN, lines[1])[1:-1]]
            # 如果第一行有空格或者键的重复，使用默认值填充
            else:
                cc = []
                i = 0
                for c in re.split(V_LINE_PATTERN, lines[1])[1:-1]:
                    cs = c.strip()
                    if cs == "" or cs in cc:
                        cc.append(_("组合" + CHINESE_NUM[i]))
                        i += 1
                    else:
                        for k in TRANS_DICT.values():
                            if cs in k:
                                cc.append(textwrap.fill(k, 10))
                                break
                        else:
                            cc.append(cs)
        w = [len(c) + 2 for c in re.split(V_LINE_PATTERN, lines[0])[1:-1]]

        assert len(w) == len(cc)
        if len(cc) >= 5:
            _header = from_list(gen_header(cc, w, self._cpx_headers), False)
            return vstack(_header, nt)
        else:
            return table

    def get_string(self):
        self._base_info()
        self.ops_dispatch()
        return str(self.body)

    def process_body(self, t, maxrows=30):
        """处理表格主体
        分别为多表,单双栏做法
        """
        if self.is_zh:
            t.align = "c"
        else:
            t.align = "r"
        t._align["Field 1"] = "l"  # 破坏了封装 左对齐

        if self.can_vstack:  # 多表
            num = random.randint(2, 4)  # 表格数量
            out = []
            if self.is_zh:
                w = max(t.table_width, self._info.table_width) - 2
            else:
                w = t.table_width
            for i in range(num):
                _max = maxrows // num
                step = random.randint(_max // 2, _max)
                start = random.randint(0, maxrows - _max)
                new = t[start : start + step]
                if self.is_zh:
                    new.table_width = t.table_width
                if hit(0.3):
                    new = self.build_complex_header(new)
                out.append(new)
                if self.is_zh:
                    random_text = wrap("    " + random_words(), w)
                else:
                    random_text = textwrap.fill(self.faker.paragraph(6), w)
                out.append(random_text)
            t = vstack(out)
        else:
            if self.can_hstack:
                new = AwesomeTable()
                new.add_row(t._rows[0] + t._rows[0])
                mid = (len(t._rows) - 1) // 2
                for i in range(1, mid):
                    new.add_row(t._rows[i] + t._rows[i + mid])
                new._align["Field 1"] = "l"
                new._align["Field %d" % (len(t._rows[0]) + 1)] = "l"
                t = new
                t.max_width = 30

            elif self.can_truncate:  # 截断
                # t.sort_key = lambda x: random.random()
                # t.sortby = 'Field 1'
                t = t[:maxrows]
            ##
            if self._table_width:
                t.table_width = self._table_width

            if self.can_complex:  # 表头
                t = self.build_complex_header(t, t._rows[0])
        self.table_width = str(t).splitlines()[0].__len__()
        return t

    @property
    def table(self):
        self._base_info()
        self.ops_dispatch()

        if self.can_vstack:
            return vstack([self.title, self.info, self.body])
        else:
            return vstack([self.title, self.info, self.body, self.footer])

    def get_image(self):

        return table2image(self.table, line_pad=-1, offset=10)

    def create(self, batch, page_it=False):
        if not page_it:
            for i in range(batch):
                yield self.table
        else:
            lpp = _compute_lines_per_page(self.table)
            for i in range(batch):
                for t in paginate(self.table, lpp):
                    yield t


def gen_header(c, w, h=tuple(range(5))):
    """枚举复杂表头格式
    不要试图去优化这段代码,<arry_lee@qq.com>
    """
    if len(c) == 5:
        t1 = [
            {c[0]: w[0]},
            {h[0]: {c[1]: w[1], c[2]: w[2]}},
            {h[1]: {c[3]: w[3], c[4]: w[4]}},
        ]
        t2 = [{c[0]: w[0]}, {h[0]: {c[1]: w[1], c[2]: w[2], c[3]: w[3], c[4]: w[4]}}]
        t3 = [
            {c[0]: w[0]},
            {h[0]: {h[0]: {c[1]: w[1], c[2]: w[2]}, h[1]: {c[3]: w[3], c[4]: w[4]}}},
        ]
        t = random.choice([t1, t2, t3])
    elif len(c) == 6:
        t1 = [
            {c[0]: w[0]},
            {h[0]: {c[1]: w[1], c[2]: w[2]}},
            {c[3]: w[3]},
            {h[1]: {c[4]: w[4], c[5]: w[5]}},
        ]
        t2 = [
            {c[0]: w[0]},
            {h[0]: {c[1]: w[1], c[2]: w[2], c[3]: w[3], c[4]: w[4], c[5]: w[5]}},
        ]
        t3 = [
            {c[0]: w[0]},
            {
                h[0]: {
                    h[1]: {c[1]: w[1], c[2]: w[2]},
                    h[2]: {c[3]: w[3], c[4]: w[4]},
                    c[5]: w[5],
                }
            },
        ]
        t = random.choice([t1, t2, t3])
    elif len(c) == 7:
        t1 = [
            {c[0]: w[0]},
            {h[0]: {h[2]: {c[1]: w[1], c[2]: w[2]}, c[3]: w[3]}},
            {h[1]: {h[2]: {c[4]: w[4], c[5]: w[5]}, c[6]: w[6]}},
        ]
        t2 = [
            {c[0]: w[0]},
            {
                h[0]: {
                    h[2]: {c[1]: w[1], c[2]: w[2]},
                    c[3]: w[3],
                    h[3]: {c[4]: w[4], c[5]: w[5]},
                    c[6]: w[6],
                }
            },
        ]
        t = random.choice([t1, t2])
    elif len(c) == 8:
        t1 = [
            {c[0]: w[0]},
            {h[0]: {h[2]: {c[1]: w[1], c[2]: w[2]}, c[3]: w[3]}},
            {h[1]: {h[2]: {c[4]: w[4], c[5]: w[5]}, c[6]: w[6], c[7]: w[7]}},
        ]
        t2 = [
            {c[0]: w[0]},
            {
                h[0]: {
                    h[1]: {c[1]: w[1], c[2]: w[2], c[3]: w[3]},
                    h[2]: {c[4]: w[4], c[5]: w[5]},
                    h[3]: {c[6]: w[6], c[7]: w[7]},
                }
            },
        ]
        t = random.choice([t1, t2])
    elif len(c) == 9:
        t1 = [
            {c[0]: w[0]},
            {h[0]: {h[2]: {c[1]: w[1], c[2]: w[2]}, c[3]: w[3], c[4]: w[4]}},
            {h[1]: {h[2]: {c[5]: w[5], c[6]: w[6]}, c[7]: w[7], c[8]: w[8]}},
        ]
        t2 = [
            {c[0]: w[0]},
            {h[0]: {h[2]: {c[1]: w[1], c[2]: w[2]}, h[3]: {c[3]: w[3], c[4]: w[4]}}},
            {h[1]: {h[2]: {c[5]: w[5], c[6]: w[6]}, h[3]: {c[7]: w[7], c[8]: w[8]}}},
        ]
        t3 = [
            {c[0]: w[0]},
            {
                h[0]: {
                    h[1]: {c[1]: w[1], c[2]: w[2]},
                    h[2]: {c[3]: w[3], c[4]: w[4]},
                    h[3]: {c[5]: w[5], c[6]: w[6]},
                    h[4]: {c[7]: w[7], c[8]: w[8]},
                }
            },
        ]
        t = random.choice([t1, t2, t3])
    elif len(c) == 10:
        t1 = [
            {c[0]: w[0]},
            {h[0]: {h[2]: {c[1]: w[1], c[2]: w[2]}, h[3]: {c[3]: w[3], c[4]: w[4]}}},
            {
                h[1]: {
                    h[2]: {c[5]: w[5], c[6]: w[6]},
                    h[3]: {c[7]: w[7], c[8]: w[8], c[9]: w[9]},
                }
            },
        ]
        t2 = [
            {c[0]: w[0]},
            {h[0]: {h[2]: {c[1]: w[1], c[2]: w[2]}, c[3]: w[3], c[4]: w[4]}},
            {
                h[1]: {
                    h[2]: {c[5]: w[5], c[6]: w[6]},
                    c[7]: w[7],
                    c[8]: w[8],
                    c[9]: w[9],
                }
            },
        ]
        t3 = [
            {c[0]: w[0]},
            {
                h[0]: {
                    h[1]: {c[1]: w[1], c[2]: w[2]},
                    h[2]: {c[3]: w[3], c[4]: w[4]},
                    h[3]: {c[5]: w[5], c[6]: w[6]},
                    h[4]: {c[7]: w[7], c[8]: w[8], c[9]: w[9]},
                }
            },
        ]
        t = random.choice([t1, t2, t3])
    elif len(c) == 11:
        t1 = [
            {c[0]: w[0]},
            {
                h[0]: {
                    h[2]: {c[1]: w[1], c[2]: w[2]},
                    h[3]: {c[3]: w[3], c[4]: w[4]},
                    c[5]: w[5],
                }
            },
            {
                h[1]: {
                    h[2]: {c[6]: w[6], c[7]: w[7]},
                    h[3]: {c[8]: w[8], c[9]: w[9]},
                    c[10]: w[10],
                }
            },
        ]
        t2 = [
            {c[0]: w[0]},
            {
                h[0]: {
                    h[1]: {c[1]: w[1], c[2]: w[2]},
                    h[2]: {c[3]: w[3], c[4]: w[4]},
                    h[3]: {c[5]: w[5], c[6]: w[6], c[7]: w[7]},
                    h[4]: {c[8]: w[8], c[9]: w[9], c[10]: w[10]},
                }
            },
        ]
        t = random.choice([t1, t2])
    elif len(c) == 12:
        t1 = [
            {c[0]: w[0]},
            {
                h[0]: {
                    h[2]: {c[1]: w[1], c[2]: w[2]},
                    h[3]: {c[3]: w[3], c[4]: w[4]},
                    c[5]: w[5],
                }
            },
            {
                h[1]: {
                    h[2]: {c[6]: w[6], c[7]: w[7]},
                    h[3]: {c[8]: w[8], c[9]: w[9]},
                    c[10]: w[10],
                    c[11]: w[11],
                }
            },
        ]
        t2 = [
            {c[0]: w[0]},
            {
                h[0]: {
                    h[1]: {c[1]: w[1], c[2]: w[2]},
                    h[2]: {c[3]: w[3], c[4]: w[4], c[5]: w[5]},
                    h[3]: {c[6]: w[6], c[7]: w[7]},
                    h[4]: {c[8]: w[8], c[9]: w[9]},
                    c[10]: w[10],
                    c[11]: w[11],
                }
            },
        ]
        t = random.choice([t1, t2])
    elif len(c) == 13:
        t1 = [
            {c[0]: w[0]},
            {
                h[0]: {
                    h[2]: {c[1]: w[1], c[2]: w[2]},
                    h[3]: {c[3]: w[3], c[4]: w[4]},
                    c[5]: w[5],
                    c[6]: w[6],
                }
            },
            {
                h[1]: {
                    h[2]: {c[7]: w[7], c[8]: w[8]},
                    h[3]: {c[9]: w[9], c[10]: w[10]},
                    c[11]: w[11],
                    c[12]: w[12],
                }
            },
        ]
        t2 = [
            {c[0]: w[0]},
            {
                h[0]: {
                    h[1]: {c[1]: w[1], c[2]: w[2]},
                    h[2]: {c[3]: w[3], c[4]: w[4]},
                    c[5]: w[5],
                    c[6]: w[6],
                    h[3]: {c[7]: w[7], c[8]: w[8]},
                    h[4]: {c[9]: w[9], c[10]: w[10]},
                    c[11]: w[11],
                    c[12]: w[12],
                }
            },
        ]
        t = random.choice([t1, t2])
    elif len(c) == 14:
        t1 = [
            {c[0]: w[0]},
            {
                h[0]: {
                    h[2]: {c[1]: w[1], c[2]: w[2]},
                    h[3]: {c[3]: w[3], c[4]: w[4]},
                    c[5]: w[5],
                    c[6]: w[6],
                }
            },
            {
                h[1]: {
                    h[2]: {c[7]: w[7], c[8]: w[8]},
                    h[3]: {c[9]: w[9], c[10]: w[10]},
                    c[11]: w[11],
                    c[12]: w[12],
                    c[13]: w[13],
                }
            },
        ]
        t2 = [
            {c[0]: w[0]},
            {
                h[0]: {
                    h[1]: {c[1]: w[1], c[2]: w[2]},
                    h[2]: {c[3]: w[3], c[4]: w[4]},
                    c[5]: w[5],
                    c[6]: w[6],
                    h[3]: {c[7]: w[7], c[8]: w[8]},
                    h[4]: {c[9]: w[9], c[10]: w[10]},
                    c[11]: w[11],
                    c[12]: w[12],
                    c[13]: w[13],
                }
            },
        ]
        t = random.choice([t1, t2])
    else:
        raise KeyError()
    return t


def _compute_lines_per_page(table, fontsize=40, line_pad=-5):
    lines = str(table).splitlines()
    w = str_block_width(lines[0]) * fontsize // 2
    h = len(lines) * (fontsize + line_pad)
    if h > w:
        paper = Paper(direction="v")
    else:
        paper = Paper(direction="h", offset=10)
    box = paper.box
    ww, hh = box[2] - box[0], box[3] - box[1]
    lines = int(hh * (w / ww) / (fontsize + line_pad))
    return lines // 2


# 中
def fstable2image(
    table,
    xy=None,
    font_size=20,
    bgcolor="white",
    offset=0,
    background=None,
    bg_box=None,
    font_path="simfang.ttf",
    line_pad=-2,
    line_height=None,
    vrules="ALL",
    hrules="ALL",
    DEBUG=False,
    sealed=True,
    bold_pattern=None,
    back_pattern=None,
):
    """
    将财务报表渲染成图片
    """
    assert font_size % 4 == 0
    lines = str(table).splitlines()
    char_width = font_size // 2  # 西文字符宽度
    half_char_width = char_width // 2

    if line_height is None:
        line_height = font_size + line_pad

    w = (len(lines[0]) + 1) * char_width + char_width * offset * 2  # 图片宽度
    h = (len(lines) + 6) * line_height  # 图片高度

    if background and bg_box:
        x1, y1, x2, y2 = bg_box
        w0, h0 = x2 - x1, y2 - y1
        background = Image.open(background)
        wb, hb = background.size
        wn, hn = int(wb * w / w0), int(hb * h / h0)
        background = background.resize((wn, hn))
        x0, y0 = int(x1 * w / w0), int(y1 * h / h0)
    else:
        background = Image.new("RGB", (w, h), bgcolor)
        x0, y0 = xy or (char_width + char_width * offset, char_width)

    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(font_path, font_size)

    title_font = ImageFont.truetype("simhei.ttf", font_size + 10)
    subtitle_font = ImageFont.truetype("simkai.ttf", font_size - 2)
    handwrite_fonts = [
        ImageFont.truetype("./static/fonts/shouxie.ttf", font_size + 10),
        ImageFont.truetype("./static/fonts/shouxie1.ttf", font_size + 10),
        ImageFont.truetype("./static/fonts/shouxie2.ttf", font_size + 10),
    ]
    bold_font = ImageFont.truetype("simkai.ttf", font_size)
    text_font = ImageFont.truetype(font_path, font_size)

    cell_boxes = set()  # 多行文字的外框是同一个，需要去重
    text_boxes = []  # 文本框
    seals = []  # 统一盖章信息
    box_dict = defaultdict(list)  # 单元格映射到文本内容
    table_boxes = []  # 记录多表格的表格坐标
    lx, ty, rx, by = w, h, 0, 0  # 记录表格四极

    v = y0
    sum_diff = 0

    is_header_line = False
    header_boxes = set()

    for lno, line in enumerate(lines):
        start = half_char_width + x0
        cells = re.split(V_LINE_PATTERN, line)[1:-1]

        if lno == 6 or (lno != 0 and line[0] == "╔"):
            is_header_line = True

        if lno != 6 and line[0] == "╠":
            is_header_line = False

        if "═" in line:
            v += line_height
            continue

        if not cells:  # 处理中间大段文字
            draw.text((start, v), line, font=text_font, fill="black", anchor="lm")
            text_box = draw.textbbox((start, v), line, font=text_font, anchor="lm")
            space_cnt = 0
            while line[space_cnt] == " ":
                space_cnt += 1
            if space_cnt:
                text_box = (
                    text_box[0] + space_cnt * font_size // 2,
                    text_box[1],
                    text_box[2],
                    text_box[3],
                )
            text_boxes.append([text_box, "text@" + line])

            if (lx, ty, rx, by) != (w, h, 0, 0):
                table_boxes.append([lx, ty, rx, by])
                if DEBUG:
                    draw.rectangle([lx, ty, rx, by], outline="red", width=5)
                lx, ty, rx, by = w, h, 0, 0  # 记录表格坐标
            v += line_height
            v += 10
            sum_diff += 10
            continue

        if lno == 1:  # title
            title = cells[0].strip()
            draw.text((w // 2, v), title, font=title_font, fill="black", anchor="mm")
            titlebox = draw.textbbox((w // 2, v), title, font=title_font, anchor="mm")
            text_boxes.append([titlebox, "text@" + title])
            if DEBUG:
                draw.rectangle(titlebox, outline="green")
            v += line_height
            continue

        if lno == 3:
            date = cells[0].strip()
            draw.text((w // 2, v), date, font=font, fill="black", anchor="mm")
            titlebox = draw.textbbox((w // 2, v), date, font=font, anchor="mm")
            text_boxes.append([titlebox, "text@" + date])
            if DEBUG:
                draw.rectangle(titlebox, outline="green")
            v += line_height
            continue

        if lno == 5:
            company, info = cells[0].strip(), cells[1].strip()
            draw.text((x0, v), company, font=subtitle_font, fill="black", anchor="lm")
            titlebox = draw.textbbox((x0, v), company, font=subtitle_font, anchor="lm")
            text_boxes.append([titlebox, "text@" + company])
            seals.append((titlebox, company[5:]))
            draw.text((w - x0, v), info, font=subtitle_font, fill="black", anchor="rm")
            titlebox = draw.textbbox((w - x0, v), info, font=subtitle_font, anchor="rm")
            text_boxes.append([titlebox, "text@" + info])
            if DEBUG:
                draw.rectangle(titlebox, outline="green")
            v += line_height
            continue

        # 以下内容将不会包含'═'
        for cno, cell in enumerate(cells):
            ll = sum(str_block_width(c) + 1 for c in cells[:cno]) + 1
            if cell == "":  #
                start += char_width
                continue
            box = draw.textbbox((start, v), cell, font=font, anchor="lm")
            striped_cell = cell.strip()
            if box[1] != box[3]:
                if "〇" in cell:  # 手写签名
                    name = striped_cell.strip("〇")
                    handwritefont = handwrite_fonts.pop()
                    draw.text(
                        ((box[0] + box[2]) // 2, v),
                        name,
                        font=handwritefont,
                        fill="black",
                        anchor="mm",
                    )
                    box = draw.textbbox(
                        ((box[0] + box[2]) // 2, v),
                        name,
                        font=handwritefont,
                        anchor="mm",
                    )
                    text_boxes.append([box, "script@" + name])
                    seals.append((box, name))
                else:
                    if bold_pattern and re.match(bold_pattern, cell.strip()):
                        draw.text(
                            (start, v), cell, font=bold_font, fill="black", anchor="lm"
                        )
                    else:
                        draw.text(
                            (start, v), cell, font=font, fill="black", anchor="lm"
                        )
                    lpad, rpad = count_padding(cell)
                    l = box[0] + lpad * char_width
                    # 如果有多个空格分隔,例如无线表格
                    if "  " in striped_cell:
                        lt = l
                        for text in re.split("( {2,})", striped_cell):
                            if text.strip():
                                rt = lt + str_block_width(text) * char_width
                                text_box = (lt, box[1], rt, box[3] - 1)
                                if DEBUG:
                                    draw.rectangle(text_box, outline="green")
                                text_boxes.append([text_box, "text@" + text])
                            else:
                                lt = rt + str_block_width(text) * char_width
                    else:
                        r = box[2] - rpad * char_width
                        text_box = (l, box[1], r, box[3])
                        if DEBUG:
                            draw.rectangle(text_box, outline="green")
                        if striped_cell != "-":
                            text_boxes.append([text_box, "text@" + striped_cell])

            left = box[0] - half_char_width
            right = box[2] + half_char_width
            start = right + half_char_width
            tt = lno - 1
            bb = lno + 1
            # 原因：_str_block_width 和 [ll]不一样,解决方法，将中文替换为2个字母
            while replace_chinese_to_dunder(lines, tt)[ll] not in H_SYMBOLS:
                tt -= 1
            while replace_chinese_to_dunder(lines, bb)[ll] not in H_SYMBOLS:
                bb += 1
            if lno < len(lines) - 2:
                cbox = (
                    left,
                    tt * line_height + y0 + sum_diff,
                    right,
                    bb * line_height + y0 + sum_diff,
                )
                cell_boxes.add(cbox)
                if is_header_line:
                    header_boxes.add(cbox)
                # 记录当前的表格坐标
                lx = min(lx, cbox[0])
                ty = min(ty, cbox[1])
                rx = max(rx, cbox[2])
                by = max(by, cbox[3])

                box_dict[cbox].append(striped_cell)
        v += line_height

    if (lx, ty, rx, by) != (w, h, 0, 0):
        table_boxes.append([lx, ty, rx, by])
        if DEBUG:
            draw.rectangle([lx, ty, rx, by], outline="red", width=5)

    # 处理背景匹配
    if back_pattern:
        for box, ls in box_dict.items():
            for s in ls:
                if re.match(back_pattern, s):
                    im = Image.new(
                        "RGBA", (box[2] - box[0], box[3] - box[1]), (50, 50, 50, 100)
                    )
                    background.paste(im, box, mask=im)
                    break
    # 处理印章框
    if sealed:
        b, c = seals.pop(0)
        seal = gen_seal(c, "财务专用章", "", usestar=True)
        background, seal_box = add_seal_box(
            background, seal, (b[2], b[1] - 80), arc_seal=True
        )
        text_boxes.append([seal_box, "arc_seal@"])

        for b, n in seals:
            seal = gen_name_seal(n, font_size * 2)
            try:
                background, seal_box = add_seal_box(
                    background, seal, (b[0], b[1] - 10), arc_seal=False
                )
                text_boxes.append([seal_box, "rect_seal@"])
            except:
                pass

    cell_boxes = list(cell_boxes)
    # 以下处理标注
    for box in table_boxes:
        text_boxes.append([box, "table@"])

        draw.line((box[0], box[1]) + (box[2], box[1]), fill="black", width=2)
        draw.line((box[0], box[3]) + (box[2], box[3]), fill="black", width=2)

    for box in cell_boxes:
        text_boxes.append([box, "cell@"])
        if vrules == "ALL":
            draw.line((box[0], box[1]) + (box[0], box[3]), fill="black", width=2)
            draw.line((box[2], box[1]) + (box[2], box[3]), fill="black", width=2)

        if hrules == "ALL":
            draw.line((box[0], box[1]) + (box[2], box[1]), fill="black", width=2)
            draw.line((box[0], box[3]) + (box[2], box[3]), fill="black", width=2)
        elif hrules == "HEADER":
            if box in header_boxes:
                draw.line((box[0], box[1]) + (box[2], box[1]), fill="black", width=2)
                draw.line((box[0], box[3]) + (box[2], box[3]), fill="black", width=2)

    points = []
    cell_boxes = [tb[0] for tb in text_boxes]  # 单纯的boxes分不清是行列还是表格和文本
    label = [tb[1] for tb in text_boxes]

    for box in cell_boxes:
        points.append([box[0], box[1]])
        points.append([box[2], box[1]])
        points.append([box[2], box[3]])
        points.append([box[0], box[3]])

    return {
        "image": cv2.cvtColor(np.array(background, np.uint8), cv2.COLOR_RGB2BGR),
        "boxes": cell_boxes,  # box 和 label是一一对应的
        "label": label,
        "points": points,
    }


ORANGE = (235, 119, 46)
BLUE = (204, 237, 255)


# 将其抽象出来使得普通table能用
def fstable2image_en(
    table,
    xy=None,
    font_size=20,
    bgcolor="white",
    offset=0,
    background=None,
    bg_box=None,
    font_path="./static/fonts/simfang.ttf",
    line_pad=-2,
    line_height=None,
    vrules="ALL",
    hrules="ALL",
    DEBUG=False,
    sealed=True,
    underline_color=ORANGE,
    striped_color=BLUE,
    bold_pattern=None,
    back_pattern=None,
):
    """
    将财务报表渲染成图片
    """
    assert font_size % 4 == 0  # 图个方便

    char_width = font_size // 2  # 西文字符宽度
    half_char_width = char_width // 2

    if line_height is None:
        line_height = font_size + line_pad

    lines = str(table).splitlines()
    w = (len(lines[0]) + 1) * char_width + char_width * offset * 2  # 图片宽度
    h = (len(lines) + 6) * line_height  # 图片高度

    if background is not None and bg_box:
        x1, y1, x2, y2 = bg_box
        w0, h0 = x2 - x1, y2 - y1
        background = Image.open(background)
        wb, hb = background.size
        wn, hn = int(wb * w / w0), int(hb * h / h0)
        background = background.resize((wn, hn))
        x0, y0 = int(x1 * w / w0), int(y1 * h / h0)
    else:
        background = Image.new("RGB", (w, h), bgcolor)
        x0, y0 = xy or (char_width + char_width * offset, char_width)

    if hit(0.3):  # 三种风格的比例为1:1:1
        underline_color = None
        striped_color = None
        need_striped = False
    else:
        if hit(0.5):
            underline_color = None
            need_striped = True
        else:
            striped_color = None
            need_striped = False

    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(font_path, font_size)

    en_font = ImageFont.truetype("arial.ttf", font_size)
    title_font = ImageFont.truetype("ariblk.ttf", font_size + 12)
    subtitle_font = ImageFont.truetype("ariali.ttf", font_size - 2)
    # handwrite_fonts = [
    #     ImageFont.truetype('./static/fonts/shouxie.ttf', font_size + 10),
    #     ImageFont.truetype('./static/fonts/shouxie1.ttf', font_size + 10),
    #     ImageFont.truetype('./static/fonts/shouxie2.ttf', font_size + 10)]
    bold_font = ImageFont.truetype("arialbi.ttf", font_size)
    text_font = ImageFont.truetype("simfang.ttf", font_size)

    cell_boxes = set()  # 多行文字的外框是同一个，需要去重
    text_boxes = []  # 文本框
    seals = []  # 统一盖章信息
    box_dict = defaultdict(list)  # 单元格映射到文本内容
    table_boxes = []  # 记录多表格的表格坐标
    lx, ty, rx, by = w, h, 0, 0  # 记录表格四极

    v = y0
    sum_diff = 0

    TITLE_LINE_NO = 1
    SUBTITLE_LINE_NO = 3
    INFO_LINE_NO = 5
    HEADER_START_LINE_NO = 7

    i = HEADER_START_LINE_NO
    try:
        while lines[i][0] != "╠":
            i += 1
    except:
        pass
    HEADER_END_LINE_NO = i

    for lno, line in enumerate(lines):
        start = half_char_width + x0
        cells = re.split(V_LINE_PATTERN, line)[1:-1]

        if "═" in line:
            v += line_height
            continue

        if not cells:  # 处理中间大段文字
            draw.text((start, v), line, font=text_font, fill="black", anchor="lm")
            text_box = draw.textbbox((start, v), line, font=text_font, anchor="lm")
            space_cnt = 0
            while line[space_cnt] == " ":
                space_cnt += 1
            if space_cnt:
                text_box = (
                    text_box[0] + space_cnt * font_size // 2,
                    text_box[1],
                    text_box[2],
                    text_box[3],
                )
            text_boxes.append([text_box, "text@" + line])

            if (lx, ty, rx, by) != (w, h, 0, 0):
                table_boxes.append([lx, ty, rx, by])
                if DEBUG:
                    draw.rectangle([lx, ty, rx, by], outline="red", width=5)
                lx, ty, rx, by = w, h, 0, 0  # 记录表格坐标
            v += line_height
            v += 5
            sum_diff += 5
            continue

        if lno == TITLE_LINE_NO:  # title
            title = cells[0].strip()
            draw.text((start, v), title, font=title_font, fill="black", anchor="lm")
            titlebox = draw.textbbox((start, v), title, font=title_font, anchor="lm")
            text_boxes.append([titlebox, "text@" + title])
            if DEBUG:
                draw.rectangle(titlebox, outline="green")
            v += line_height
            continue

        if lno == SUBTITLE_LINE_NO:
            date = cells[0].strip()
            draw.text((start, v), date, font=subtitle_font, fill="black", anchor="lm")
            titlebox = draw.textbbox((start, v), date, font=subtitle_font, anchor="lm")
            text_boxes.append([titlebox, "text@" + date])
            if DEBUG:
                draw.rectangle(titlebox, outline="green")
            v += line_height
            continue

        if lno == INFO_LINE_NO:
            # company, info = cells[0].strip(), cells[1].strip()
            # draw.text((x0, v), company, font=subtitle_font, fill='black',
            #           anchor='lm')
            # titlebox = draw.textbbox((x0, v), company, font=subtitle_font,
            #                          anchor='lm')
            # text_boxes.append([titlebox, 'text@' + company])
            # seals.append((titlebox, company[5:]))
            # draw.text((w - x0, v), info, font=subtitle_font, fill='black',
            #           anchor='rm')
            # titlebox = draw.textbbox((w - x0, v), info, font=subtitle_font,
            #                          anchor='rm')
            # text_boxes.append([titlebox, 'text@' + info])
            # if DEBUG:
            #     draw.rectangle(titlebox, outline='green')
            v += line_height
            continue

        need_striped = not need_striped  # 切换条纹
        if lno < HEADER_END_LINE_NO:  # 表头无条纹
            need_striped = False

        for cno, cell in enumerate(cells):
            ll = sum(str_block_width(c) + 1 for c in cells[:cno]) + 1
            if cell == "":  #
                start += char_width
                continue
            box = draw.textbbox((start, v), cell, font=font, anchor="lm")

            # 条纹背景
            if striped_color and need_striped:
                draw.rectangle(
                    (
                        box[0] - char_width,
                        v - font_size // 2 + 2,
                        box[2] + char_width,
                        v + font_size // 2 - 2,
                    ),
                    fill=striped_color,
                )

            striped_cell = cell.strip()
            if box[1] != box[3]:
                # 用英文重写,左对齐，右对齐
                if HEADER_START_LINE_NO <= lno < HEADER_END_LINE_NO:
                    _font = bold_font
                    _color = "black"
                elif lno % 7 == 2 and lno > HEADER_END_LINE_NO + 1:
                    _font = bold_font
                    _color = underline_color or "black"
                else:
                    _font = en_font
                    _color = "black"

                if striped_cell != "ITEM":  # fix issue7
                    if cno == 0:
                        draw.text(
                            (box[0], box[1]), cell.rstrip(), _color, _font, anchor="lt"
                        )
                        _box = draw.textbbox(
                            (box[0], box[1]), cell.rstrip(), _font, anchor="lt"
                        )
                        text_box = draw.textbbox(
                            (_box[2], _box[1]), cell.strip(), _font, anchor="rt"
                        )
                    else:
                        draw.text(
                            (box[2], box[1]), cell.lstrip(), _color, _font, anchor="rt"
                        )
                        _box = draw.textbbox(
                            (box[2], box[1]), cell.lstrip(), _font, anchor="rt"
                        )
                        text_box = draw.textbbox(
                            (_box[0], _box[1]), cell.strip(), _font, anchor="lt"
                        )

                lpad, rpad = count_padding(cell)
                l = box[0] + lpad * char_width
                # 如果有多个空格分隔,例如无线表格
                if "  " in striped_cell:
                    lt = l
                    for text in re.split("( {2,})", striped_cell):
                        if text.strip():
                            rt = lt + str_block_width(text) * char_width
                            text_box = (lt, box[1], rt, box[3] - 1)
                            if DEBUG:
                                draw.rectangle(text_box, outline="green")
                            text_boxes.append([text_box, "text@" + text])
                        else:
                            lt = rt + str_block_width(text) * char_width
                else:
                    r = box[2] - rpad * char_width
                    if striped_cell != "ITEM":
                        if DEBUG:
                            draw.rectangle(text_box, outline="green")
                        if striped_cell != "-":
                            text_boxes.append([text_box, "text@" + striped_cell])

            left = box[0] - half_char_width
            right = box[2] + half_char_width
            start = right + half_char_width
            tt = lno - 1
            bb = lno + 1
            # 原因：_str_block_width 和 [ll]不一样,解决方法，将中文替换为2个字母
            while replace_chinese_to_dunder(lines, tt)[ll] not in H_SYMBOLS:
                tt -= 1
            while replace_chinese_to_dunder(lines, bb)[ll] not in H_SYMBOLS:
                bb += 1
            if lno < len(lines) - 2:
                cbox = (
                    left,
                    tt * line_height + y0 + sum_diff,
                    right,
                    bb * line_height + y0 + sum_diff,
                )
                cell_boxes.add(cbox)
                margin = char_width
                if HEADER_START_LINE_NO <= lno < HEADER_END_LINE_NO:
                    draw.line(
                        (cbox[0] + margin, cbox[3]) + (cbox[2] - margin, cbox[3]),
                        fill="black",
                        width=3,
                    )
                elif lno % 7 == 2 and lno > HEADER_END_LINE_NO + 1:
                    draw.line(
                        (cbox[0] + margin, cbox[1]) + (cbox[2] - margin, cbox[1]),
                        fill=underline_color,
                        width=3,
                    )
                    draw.line(
                        (cbox[0] + margin, cbox[3]) + (cbox[2] - margin, cbox[3]),
                        fill=underline_color,
                        width=3,
                    )

                # 记录当前的表格坐标
                lx = min(lx, cbox[0])
                ty = min(ty, cbox[1])
                rx = max(rx, cbox[2])
                by = max(by, cbox[3])

                box_dict[cbox].append(striped_cell)

                if striped_cell == "ITEM" and cno == 0:  # fixed issue#7
                    if random.random() < 0.5:  # 0.5 的概率出现
                        x_ = random.randint(cbox[0], (cbox[2] + cbox[0]) // 2)
                        y_pool = [cbox[3]]
                        i = 1
                        while True:
                            if cbox[1] + i * line_height < (cbox[1] + cbox[3]) // 2:
                                y_pool.append(cbox[1] + i * line_height)
                                i += 1
                            else:
                                break
                        y_ = random.choice(y_pool)
                        draw.text((x_, y_), striped_cell, _color, _font, anchor="lb")
                        text_box = draw.textbbox(
                            (x_, y_), striped_cell, _font, anchor="lb"
                        )
                        text_boxes.append([text_box, "text@" + striped_cell])

        v += line_height

    if (lx, ty, rx, by) != (w, h, 0, 0):
        table_boxes.append([lx, ty, rx, by])
        if DEBUG:
            draw.rectangle([lx, ty, rx, by], outline="red", width=5)

    # 处理背景匹配
    if back_pattern:
        for box, ls in box_dict.items():
            for s in ls:
                if re.match(back_pattern, s):
                    im = Image.new(
                        "RGBA", (box[2] - box[0], box[3] - box[1]), (50, 50, 50, 100)
                    )
                    background.paste(im, box, mask=im)
                    break

    cell_boxes = list(cell_boxes)
    # 以下处理标注
    for cbox in table_boxes:
        text_boxes.append([cbox, "table@"])

        draw.line((cbox[0], cbox[1]) + (cbox[2], cbox[1]), fill="black", width=2)
        draw.line(
            (cbox[0], cbox[1] - 4) + (cbox[2], cbox[1] - 4), fill="black", width=2
        )
        draw.line((cbox[0], cbox[3]) + (cbox[2], cbox[3]), fill="black", width=2)
        draw.line(
            (cbox[0], cbox[3] - 4) + (cbox[2], cbox[3] - 4), fill="black", width=2
        )
    for box in cell_boxes:
        text_boxes.append([box, "cell@"])
        # margin = char_width
        # if underline_color:
        #     draw.line((box[0]+margin, box[3]) + (box[2]-margin, box[3]), fill=underline_color,
        #               width=3)
        # if vrules == 'ALL':
        #     draw.line((box[0], box[1]) + (box[0], box[3]), fill='black',
        #               width=2)
        #     draw.line((box[2], box[1]) + (box[2], box[3]), fill='black',
        #               width=2)
        # if hrules == 'ALL':
        #     draw.line((box[0], box[1]) + (box[2], box[1]), fill='black',
        #               width=2)
        #     draw.line((box[0], box[3]) + (box[2], box[3]), fill='black',
        #               width=2)

    points = []
    cell_boxes = [tb[0] for tb in text_boxes]  # 单纯的boxes分不清是行列还是表格和文本
    label = [tb[1] for tb in text_boxes]

    for box in cell_boxes:
        points.append([box[0], box[1]])
        points.append([box[2], box[1]])
        points.append([box[2], box[3]])
        points.append([box[0], box[3]])
    return {
        "image": cv2.cvtColor(np.array(background, np.uint8), cv2.COLOR_RGB2BGR),
        "boxes": cell_boxes,  # box 和 label是一一对应的
        "label": label,
        "points": points,
    }


if __name__ == "__main__":
    f = FinancialStatementTable("Consolidated Balance Sheet", lang="en")
    t = f.table
    data = f.get_image()

    cv2.imwrite("t.jpg", data)
