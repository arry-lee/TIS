import random
import re
from collections import defaultdict
from functools import lru_cache
from itertools import cycle

import cv2
import faker
import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont
from toolz import partition_all

from awesometable import (AwesomeTable, H_SYMBOLS, __c, _count_padding,
                          _str_block_width, from_list, paginate,
                          vpat, vstack, wrap)
from post_processor.A4 import Paper
from post_processor.seal import add_seal, gen_name_seal, gen_seal
from utils.ulpb import encode

CHINESE_NUM = '一二三四五六七八九十'

# RANDOM_SEED = 42
# random.seed(RANDOM_SEED)
# faker.Faker.seed(RANDOM_SEED)
LANG = 'zh_CN'
if LANG == 'zh_CN':
    fp = r'./static/pdf/sentence.txt'
    words = []
    with open(fp, encoding='utf-8') as f:
        for s in f.read().split():
            if len(s) > 30:
                words.append(s)
else:
    fp = r'./static/pdf/sentence-en.txt'
    words = []
    with open(fp, encoding='utf-8') as f:
        for s in f.read().split('.'):
            if len(s) > 30:
                words.append(s)

random_words = lambda:random.choice(words)
random_price = lambda:'{:,}'.format(random.randint(10000000, 1000000000))
hit = lambda r:random.random() <= r

if LANG == 'zh_CN':
    def _(x):
        return x
else:
    @lru_cache
    def _(x): # translate
        return encode(x).title()


def random_dic(dicts):
    dict_key_ls = list(dicts.keys())
    random.shuffle(dict_key_ls)
    new_dic = {}
    for key in dict_key_ls:
        v = dicts.get(key)
        if isinstance(v, dict):
            v = random_dic(v)
        new_dic[key] = v
    return new_dic


def build_complex_header(headers, columns):
    """根据headers 和 columns 构建复杂表头字典"""
    inner = {}
    for ino, h, keys in zip(range(len(headers)),
                            reversed(headers),
                            partition_all(len(columns) // len(headers),
                                          columns)):
        if ino == 0:
            inner = {h:dict.fromkeys(keys)}
        else:
            inner = {h:{**inner, **dict.fromkeys(keys)}}
    return inner


def build_complex_header_w(headers, columns, widths):
    """
    headers 标题list
    columns 列名list
    widths  列宽list
    """
    inner = {}
    for ino, h, keys, ws in zip(range(len(headers)),
                                reversed(headers),
                                partition_all(len(columns) // len(headers),
                                              columns),
                                partition_all(len(columns) // len(headers),
                                              widths)):
        if ino == 0:
            inner = {h:{k:v for k, v in zip(keys, ws)}}

        else:
            inner = {h:{**inner, **{k:v for k, v in zip(keys, ws)}}}
    return inner


class FinancialStatementTable(object):
    """财报统一生成接口"""

    common_columns = [[_('项目'), _('本期发生额'), _('上期发生额')],
                      [_('项目'), _('本月实际'), _('本年累计'), _('上年同期')],
                      [_('项目'), _('行次'), _('本月实际'), _('本年累计'), _('上年同期')],
                      [_('项目'), _('附注'), _('本月实际'), _('本年累计'), _('上年同期')],
                      [_('项目'), _('实收资本(或股本)'), _('资本公积'), _('其他综合收益'),
                       _('盈余公积')],
                      [_('项目'), _('实收资本(或股本)'), _('资本公积'), _('其他综合收益'),
                       _('盈余公积'), _('一般风险准备')],
                      [_('项目'), _('实收资本(或股本)'), _('资本公积'), _('其他综合收益'),
                       _('盈余公积'), _('一般风险准备'), _('未分配利润')]
                      ]

    def __init__(self, name, lang=LANG):
        self.faker = faker.Faker(lang)
        self.lang = lang
        if lang == 'zh_CN':
            config = './config/financial_statement_config.yaml'
        else:
            config = './config/en-config.yaml'

        with open(config, 'r', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
        self.config = config
        self.name = name
        self._index = config[name]
        self._columns_generator = cycle(self.common_columns)

    def _ops_dispatch(self):
        # 对于生成的表格根据其长度分发到不同的操作
        # cols <= 3 分割重组 hstack
        # cols > 5  复杂表头
        # rows > max_perpage 截断或分页
        # rows < half_max_perpage vstack 多表
        c = len(self._columns)
        r = sum(len(v) + 1 for v in self._index.values() if v)
        rmax = 30  # 单页最大行数
        rmin = 15  # 低于此行数实行多表堆叠
        cmin = 3  # 低于此列数可以合并
        cmax = 6  # 大于此列复杂化

        self.can_hstack = hit(0.5) and r > rmax
        self.can_vstack = hit(0.5) and r > rmin
        self.can_paginate = r >= rmax and cmin < c < cmax
        self.can_truncate = True
        self.can_complex = hit(0.7) and c >= cmin

    @property
    def index(self):
        return self._index

    @property
    def columns(self):
        return self._columns

    def _base_info(self):
        self.company = self.faker.company()
        self.this_year = self.faker.date()
        self.last_year = str(int(self.this_year[:4]) - 1) + self.this_year[4:]
        self.common_columns.append([_('项目'), self.this_year, self.last_year])
        self._columns = next(self._columns_generator)  # random.choice(self.common_columns)
        self._cpx_headers = (self.this_year, self.last_year, _('组合一'), _('组合二'))
        _title = AwesomeTable()
        _title.add_rows([[self.name], [self.this_year]])
        self._title = _title
        _info = AwesomeTable()
        _info.add_row([_('编制单位:') + '%s' % self.company, _('单位：千元 币种：人民币 审计类型：未经审计')])
        self._info = _info

    @property
    def title(self):
        return self._title

    @property
    def info(self):
        return self._info

    @property
    def footer(self, name_mark='〇'):
        _footer = AwesomeTable()
        _footer.add_row([_('公司负责人：'), self.faker.name() + name_mark,
                         _('主管会计工作负责人：'), self.faker.name() + name_mark,
                         _(' 会计机构负责人：'), self.faker.name() + name_mark])
        _footer.table_width = max(_footer.table_width, self.table_width)
        return _footer

    @property
    def body(self):
        return self.process_body(self._build_table())

    def _build_table(self, indent=2, fill_ratio=0.7, brace_ratio=0.3, auto_ratio=0.5):
        t = AwesomeTable()
        columns = self.columns
        t.add_row(columns)
        rno = 1
        for k, v in self.index.items():
            t.add_row([_(k)] + [''] * (len(columns) - 1))
            if v is None: continue
            for item in v:
                row = [self._indent_item(indent, item)]
                for c in columns[1:]:
                    if c == _('行次'):
                        row.append(rno)
                        rno += 1
                    elif c == _('附注'):
                        if hit(fill_ratio):
                            row.append('({})'.format(random.choice(CHINESE_NUM)))
                        else:
                            row.append(' ')
                    else:
                        if hit(fill_ratio):
                            if hit(brace_ratio):
                                row.append('({})'.format(random_price()))
                            else:
                                row.append(random_price())
                        else:
                            row.append('-')
                t.add_row(row)
        if hit(auto_ratio):
            t.add_autoindex(fieldname='行次')
        return t

    @staticmethod
    def _indent_item(indent, item):
        if item[0] == '（':
            item = ' ' * indent * 2 + _(item)
        elif item[0].isdigit():
            item = ' ' * indent * 3 + _(item)
        else:
            item = ' ' * indent + _(item)
        return item

    def _build_complex_header(self, t):
        lines = str(t).splitlines()
        cc = [c.strip() for c in re.split(vpat, lines[1])[1:-1]]
        w = [len(c) + 2 for c in re.split(vpat, lines[0])[1:-1]]
        assert len(w) == len(cc)
        if len(cc) >= 5:
            _header = from_list(gen_header(cc, w, self._cpx_headers), False)
            return vstack(_header, t)
        else:
            return t

    def process_body(self, t):
        """ 处理表格主体
        分别为多表,单双栏做法
        """
        MAXROWS = 30
        t.align = 'c'
        t._align['Field 1'] = 'l'  # 破坏了封装 左对齐

        if self.can_vstack:  # 多表
            num = random.randint(3, 4) # 表格数量
            out = []
            for i in range(num):
                _max = MAXROWS // num
                step = random.randint(_max // 2, _max)
                start = random.randint(0, MAXROWS - _max)
                new = t[start:start + step]
                if hit(0.3):
                    new = self._build_complex_header(new)
                out.append(new)
                # 防止文字段落宽度比表格宽度小太多
                w = max(len(str(new).splitlines()[0]), self._info.table_width)+6
                random_text = wrap('    ' + random_words(), w)
                out.append(random_text)
            t = vstack(out)
        else:
            if self.can_hstack:
                new = AwesomeTable()
                new.add_row(t._rows[0] + t._rows[0])
                mid = (len(t._rows) - 1) // 2
                for i in range(1, mid):
                    new.add_row(t._rows[i] + t._rows[i + mid])
                new._align['Field 1'] = 'l'
                new._align['Field %d' % (len(t._rows[0]) + 1)] = 'l'
                t = new
                t.max_width = 30

            elif self.can_truncate:  # 截断
                # t.sort_key = lambda x: random.random()
                # t.sortby = 'Field 1'
                t = t[:MAXROWS]
            if self.can_complex:  # 表头
                t = self._build_complex_header(t)
        self.table_width = str(t).splitlines()[0].__len__()
        return t

    @property
    def table(self):
        self._base_info()
        self._ops_dispatch()
        if self.can_vstack:
            return vstack([self.title, self.info, self.body])
        else:
            return vstack([self.title, self.info, self.body, self.footer])

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
        t1 = [{c[0]:w[0]}, {h[0]:{c[1]:w[1], c[2]:w[2]}}, {h[1]:{c[3]:w[3], c[4]:w[4]}}]
        t2 = [{c[0]:w[0]}, {h[0]:{c[1]:w[1], c[2]:w[2], c[3]:w[3], c[4]:w[4]}}]
        t3 = [{c[0]:w[0]}, {h[0]:{h[0]:{c[1]:w[1], c[2]:w[2]}, h[1]:{c[3]:w[3], c[4]:w[4]}}}]
        t = random.choice([t1,t2,t3])
    elif len(c) == 6:
        t1 = [{c[0]:w[0]},{h[0]:{c[1]:w[1], c[2]:w[2]}},{c[3]:w[3]},{h[1]:{c[4]:w[4], c[5]:w[5]}}]
        t2 = [{c[0]:w[0]}, {h[0]:{c[1]:w[1], c[2]:w[2], c[3]:w[3], c[4]:w[4], c[5]:w[5]}}]
        t3 = [{c[0]:w[0]}, {h[0]:{h[1]:{c[1]:w[1], c[2]:w[2]}, h[2]:{c[3]:w[3], c[4]:w[4]}, c[5]:w[5]}}]
        t = random.choice([t1, t2, t3])
    elif len(c) == 7:
        t1 = [{c[0]:w[0]},
              {h[0]:{h[2]:{c[1]:w[1], c[2]:w[2]}, c[3]:w[3]}},
              {h[1]:{h[2]:{c[4]:w[4], c[5]:w[5]}, c[6]:w[6]}}]
        t1 = [{c[0]:w[0]},
              {h[0]:{h[2]:{c[1]:w[1], c[2]:w[2]}, c[3]:w[3],
                     h[3]:{c[4]:w[4], c[5]:w[5]}, c[6]:w[6]}}]
        t = random.choice([t1, t2])
    elif len(c) == 8:
        t1 = [{c[0]:w[0]},
              {h[0]:{h[2]:{c[1]:w[1], c[2]:w[2]}, c[3]:w[3]}},
              {h[1]:{h[2]:{c[4]:w[4], c[5]:w[5]}, c[6]:w[6], c[7]:w[7]}}]
        t2 = [{c[0]:w[0]},
              {h[0]:{h[1]:{c[1]:w[1], c[2]:w[2]}, c[3]:w[3],
                     h[2]:{c[4]:w[4], c[5]:w[5]}, c[6]:w[6], c[7]:w[7]}}]
        t = random.choice([t1, t2])
    elif len(c) == 9:
        t1 = [{c[0]:w[0]},{h[0]:{h[2]:{c[1]:w[1], c[2]:w[2]}, c[3]:w[3],c[4]:w[4]}},
              {h[1]:{h[2]:{c[5]:w[5], c[6]:w[6]}, c[7]:w[7],c[8]:w[8]}}]
        t2 = [{c[0]:w[0]},
              {h[0]:{h[2]:{c[1]:w[1], c[2]:w[2]}, h[3]:{c[3]:w[3], c[4]:w[4]}}},
              {h[1]:{h[2]:{c[5]:w[5], c[6]:w[6]}, h[3]:{c[7]:w[7], c[8]:w[8]}}}]
        t3 = [{c[0]:w[0]},
              {h[0]:{h[1]:{c[1]:w[1], c[2]:w[2]}, h[2]:{c[3]:w[3], c[4]:w[4]},
                     h[3]:{c[5]:w[5], c[6]:w[6]}, h[4]:{c[7]:w[7], c[8]:w[8]}}}]
        t = random.choice([t1, t2,t3])
    elif len(c) == 10:
        t1 = [{c[0]:w[0]},
              {h[0]:{h[2]:{c[1]:w[1], c[2]:w[2]},
                     h[3]:{c[3]:w[3], c[4]:w[4]}}},
              {h[1]:{h[2]:{c[5]:w[5], c[6]:w[6]},
                     h[3]:{c[7]:w[7], c[8]:w[8], c[9]:w[9]}}}]
        t2 = [{c[0]:w[0]},
              {h[0]:{h[2]:{c[1]:w[1], c[2]:w[2]}, c[3]:w[3],
                     c[4]:w[4]}},
              {h[1]:{h[2]:{c[5]:w[5], c[6]:w[6]}, c[7]:w[7],
                     c[8]:w[8], c[9]:w[9]}}]
        t3 = [{c[0]:w[0]},
              {h[0]:{h[1]:{c[1]:w[1], c[2]:w[2]},
                     h[2]:{c[3]:w[3], c[4]:w[4]},
                     h[3]:{c[5]:w[5], c[6]:w[6]},
                     h[4]:{c[7]:w[7], c[8]:w[8], c[9]:w[9]}}}]
        t = random.choice([t1, t2, t3])
    elif len(c) == 11:
        t1 = [{c[0]:w[0]},
              {h[0]:{h[2]:{c[1]:w[1], c[2]:w[2]},
                     h[3]:{c[3]:w[3], c[4]:w[4]}, c[5]:w[5]}},
              {h[1]:{h[2]:{c[6]:w[6], c[7]:w[7]},
                     h[3]:{c[8]:w[8], c[9]:w[9]}, c[10]:w[10]}}]
        t2 = [{c[0]:w[0]},
              {h[0]:{h[1]:{c[1]:w[1], c[2]:w[2]},
                     h[2]:{c[3]:w[3], c[4]:w[4]},
                     h[3]:{c[5]:w[5], c[6]:w[6], c[7]:w[7]},
                     h[4]:{c[8]:w[8], c[9]:w[9], c[10]:w[10]}}}]
        t = random.choice([t1, t2])
    elif len(c) == 12:
        t1 = [{c[0]:w[0]},
              {h[0]:{h[2]:{c[1]:w[1], c[2]:w[2]},
                     h[3]:{c[3]:w[3], c[4]:w[4]}, c[5]:w[5]}},
              {h[1]:{h[2] :{c[6]:w[6], c[7]:w[7]},
                     h[3] :{c[8]:w[8], c[9]:w[9]}, c[10]:w[10],
                     c[11]:w[11]}}]
        t1 = [{c[0]:w[0]},
              {h[0]:{h[1]:{c[1]:w[1], c[2]:w[2]},
                     h[2]:{c[3]:w[3], c[4]:w[4], c[5]:w[5]},
                     h[3]:{c[6]:w[6], c[7]:w[7]},
                     h[4]:{c[8]:w[8], c[9]:w[9]}, c[10]:w[10], c[11]:w[11]}}]
        t = random.choice([t1, t2])
    elif len(c) == 13:
        t1 = [{c[0]:w[0]},
              {h[0]:{h[2]:{c[1]:w[1], c[2]:w[2]},
                     h[3]:{c[3]:w[3], c[4]:w[4]}, c[5]:w[5], c[6]:w[6]}},
              {h[1]:{h[2]:{c[1]:w[1], c[2]:w[2]},
                     h[3]:{c[3]:w[3], c[4]:w[4]}, c[5]:w[5], c[6]:w[6]}}]
        t2 = [{c[0]:w[0]},
              {h[0]:{h[1]:{c[1]:w[1], c[2]:w[2]},
                     h[2]:{c[3]:w[3], c[4]:w[4]}, c[5]:w[5], c[6]:w[6],
                     h[3]:{c[7]:w[7], c[8]:w[8]},
                     h[4]:{c[9]:w[9], c[10]:w[10]}, c[11]:w[11], c[12]:w[12]}}]
        t = random.choice([t1, t2])
    else:
        raise KeyError()
    return t


def _compute_lines_per_page(table, fontsize=40, line_pad=-5):
    lines = str(table).splitlines()
    w = _str_block_width(lines[0]) * fontsize // 2
    h = len(lines) * (fontsize + line_pad)
    if h > w:
        paper = Paper(direction='v')
    else:
        paper = Paper(direction='h', offset=10)
    box = paper.box
    ww, hh = box[2] - box[0], box[3] - box[1]
    lines = int(hh * (w / ww) / (fontsize + line_pad))
    return lines // 2


def fstable2image(table,
                  xy=None,
                  font_size=20,
                  bgcolor='white',
                  offset=0,
                  background=None,
                  bg_box=None,
                  font_path="./static/fonts/simfang.ttf",
                  line_pad=-2,
                  line_height=None,
                  vrules='ALL',
                  hrules='ALL',
                  DEBUG=False,
                  sealed=True,
                  bold_pattern=None,
                  back_pattern=None):
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
    h = (len(lines) + 3) * line_height  # 图片高度

    if background and bg_box:
        x1, y1, x2, y2 = bg_box
        w0, h0 = x2 - x1, y2 - y1
        background = Image.open(background)
        wb, hb = background.size
        wn, hn = int(wb * w / w0), int(hb * h / h0)
        background = background.resize((wn, hn))
        x0, y0 = int(x1 * w / w0), int(y1 * h / h0)
    else:
        background = Image.new('RGB', (w, h), bgcolor)
        x0, y0 = xy or (char_width + char_width * offset, char_width)

    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(font_path, font_size)

    title_font = ImageFont.truetype('simhei.ttf', font_size + 10)
    subtitle_font = ImageFont.truetype('simkai.ttf', font_size - 2)
    handwrite_fonts = [
        ImageFont.truetype('./static/fonts/shouxie.ttf', font_size + 10),
        ImageFont.truetype('./static/fonts/shouxie1.ttf', font_size + 10),
        ImageFont.truetype('./static/fonts/shouxie2.ttf', font_size + 10)]
    bold_font = ImageFont.truetype('simkai.ttf', font_size)
    text_font = ImageFont.truetype(font_path, font_size - 2)

    cell_boxes = set()  # 多行文字的外框是同一个，需要去重
    text_boxes = []  # 文本框
    seals = []  # 统一盖章信息
    box_dict = defaultdict(list)  # 单元格映射到文本内容
    table_boxes = []  # 记录多表格的表格坐标
    lx, ty, rx, by = w, h, 0, 0  # 记录表格四极

    for lno, line in enumerate(lines):
        v = lno * line_height + y0
        start = half_char_width + x0
        cells = re.split(vpat, line)[1:-1]

        if not cells:  # 处理中间大段文字
            draw.text((start, v), line, font=text_font, fill='black',
                      anchor='lm')
            text_box = draw.textbbox((start, v), line, font=text_font,
                                     anchor='lm')
            text_boxes.append([text_box, 'text@' + line])

            if (lx, ty, rx, by) != (w, h, 0, 0):
                table_boxes.append([lx, ty, rx, by])
                if DEBUG:
                    draw.rectangle([lx, ty, rx, by],outline='red',width=5)
                lx, ty, rx, by = w, h, 0, 0  # 记录表格坐标
            continue

        if '═' in line:
            continue

        if lno == 1:  # title
            title = cells[0].strip()
            draw.text((w // 2, v), title, font=title_font, fill='black',
                      anchor='mm')
            titlebox = draw.textbbox((w // 2, v), title, font=title_font,
                                     anchor='mm')
            text_boxes.append([titlebox, 'text@' + title])
            if DEBUG:
                draw.rectangle(titlebox, outline='green')
            continue

        if lno == 3:
            date = cells[0].strip()
            draw.text((w // 2, v), date, font=font, fill='black',
                      anchor='mm')
            titlebox = draw.textbbox((w // 2, v), date, font=font,
                                     anchor='mm')
            text_boxes.append([titlebox, 'text@' + date])
            if DEBUG:
                draw.rectangle(titlebox, outline='green')
            continue

        if lno == 5:
            company, info = cells[0].strip(), cells[1].strip()
            draw.text((x0, v), company, font=subtitle_font, fill='black',
                      anchor='lm')
            titlebox = draw.textbbox((x0, v), company, font=subtitle_font,
                                     anchor='lm')
            text_boxes.append([titlebox, 'text@' + company])
            seals.append((titlebox, company[5:]))
            draw.text((w - x0, v), info, font=subtitle_font, fill='black',
                      anchor='rm')
            titlebox = draw.textbbox((w - x0, v), info, font=subtitle_font,
                                     anchor='rm')
            text_boxes.append([titlebox, 'text@' + info])
            if DEBUG:
                draw.rectangle(titlebox, outline='green')
            continue

        # 以下内容将不会包含'═'
        for cno, cell in enumerate(cells):
            ll = sum(_str_block_width(c) + 1 for c in cells[:cno]) + 1
            if cell == '':  #
                start += char_width
                continue
            box = draw.textbbox((start, v), cell, font=font, anchor='lm')
            striped_cell = cell.strip()
            if box[1] != box[3]:
                if '〇' in cell:  # 手写签名
                    name = striped_cell.strip('〇')
                    handwritefont = handwrite_fonts.pop()
                    draw.text(((box[0] + box[2]) // 2, v), name,
                              font=handwritefont, fill='black', anchor='mm')
                    box = draw.textbbox(((box[0] + box[2]) // 2, v), name,
                                        font=handwritefont, anchor='mm')
                    text_boxes.append([box, 'text@' + name])
                    seals.append((box, name))
                else:
                    if bold_pattern and re.match(bold_pattern, cell.strip()):
                        draw.text((start, v), cell, font=bold_font,
                                  fill='black',
                                  anchor='lm')
                    else:
                        draw.text((start, v), cell, font=font, fill='black',
                                  anchor='lm')
                    lpad, rpad = _count_padding(cell)
                    l = box[0] + lpad * char_width
                    # 如果有多个空格分隔,例如无线表格
                    if '  ' in striped_cell:
                        lt = l
                        for text in re.split('( {2,})', striped_cell):
                            if text.strip():
                                rt = lt + _str_block_width(text) * char_width
                                text_box = (lt, box[1], rt, box[3] - 1)
                                if DEBUG:
                                    draw.rectangle(text_box, outline='green')
                                text_boxes.append([text_box, 'text@' + text])
                            else:
                                lt = rt + _str_block_width(text) * char_width
                    else:
                        r = box[2] - rpad * char_width
                        text_box = (l, box[1], r, box[3])
                        if DEBUG:
                            draw.rectangle(text_box, outline='green')
                        if striped_cell != '-':
                            text_boxes.append(
                                [text_box, 'text@' + striped_cell])

            left = box[0] - half_char_width
            right = box[2] + half_char_width
            start = right + half_char_width
            tt = lno - 1
            bb = lno + 1
            # 原因：_str_block_width 和 [ll]不一样,解决方法，将中文替换为2个字母
            while __c(lines, tt)[ll] not in H_SYMBOLS: tt -= 1
            while __c(lines, bb)[ll] not in H_SYMBOLS: bb += 1
            if lno < len(lines) - 2:
                cbox = (left, tt * line_height + y0, right, bb * line_height + y0)
                cell_boxes.add(cbox)
                # 记录当前的表格坐标
                lx = min(lx, cbox[0])
                ty = min(ty, cbox[1])
                rx = max(rx, cbox[2])
                by = max(by, cbox[3])

                box_dict[cbox].append(striped_cell)


    if (lx, ty, rx, by) != (w, h, 0, 0):
        table_boxes.append([lx, ty, rx, by])
        if DEBUG:
            draw.rectangle([lx, ty, rx, by], outline='red', width=5)

    # 处理背景匹配
    if back_pattern:
        for box, ls in box_dict.items():
            for s in ls:
                if re.match(back_pattern, s):
                    im = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]),(50, 50, 50, 100))
                    background.paste(im, box, mask=im)
                    break

    cell_boxes = list(cell_boxes)
    # 以下处理标注
    for box in table_boxes:
        text_boxes.append([box, 'table@'])

    for box in cell_boxes:
        text_boxes.append([box, 'cell@'])
        if vrules == 'ALL':
            draw.line((box[0], box[1]) + (box[0], box[3]), fill='black',
                      width=2)
            draw.line((box[2], box[1]) + (box[2], box[3]), fill='black',
                      width=2)
        if hrules == 'ALL':
            draw.line((box[0], box[1]) + (box[2], box[1]), fill='black',
                      width=2)
            draw.line((box[0], box[3]) + (box[2], box[3]), fill='black',
                      width=2)

    points = []
    cell_boxes = [tb[0] for tb in text_boxes]  # 单纯的boxes分不清是行列还是表格和文本
    label = [tb[1] for tb in text_boxes]

    for box in cell_boxes:
        points.append([box[0], box[1]])
        points.append([box[2], box[1]])
        points.append([box[2], box[3]])
        points.append([box[0], box[3]])

    if sealed and LANG != 'en':
        b, c = seals.pop(0)
        seal = gen_seal(c, '财务专用章', '', usestar=True)
        background = add_seal(background, seal, (b[2], b[1] - 80))
        for b, n in seals:
            seal = gen_name_seal(n, font_size * 2)
            try:
                background = add_seal(background, seal, (b[0], b[1] - 10))
            except:
                pass

    return {
        'image' :cv2.cvtColor(np.array(background, np.uint8),cv2.COLOR_RGB2BGR),
        'boxes' :cell_boxes,  # box 和 label是一一对应的
        'label' :label,
        'points':points
        }


if __name__ == '__main__':
    # t = {'H1':{'H2':{'H3':{0:None,1:None},2:None,3:None},4:None,5:None}}
    #
    # lt = [1,[[2,[5,[6,[8,9]],7]],3,4]]

    # n = 13
    # t = gen_header(list(range(n)),[8]*n)
    # print(from_list(t,False))

    # print(from_list(lt))

    f = FinancialStatementTable("合并利润表", lang=LANG)
    t = f.table
    print(t)
    BOLD_PATTERN = re.compile(r'.*[其项合总年]*[中目计前额].*')
    BACK_PATTERN = re.compile(r'[一二三四五六七八九十]+.*')
    data = fstable2image(t, offset=10, DEBUG=True, bold_pattern=None,
                         back_pattern=None)['image']
    cv2.imwrite('t.jpg', data)

# FONT_MAP = [(re.compile(r'.*：$'), ('simhei.ttf', 40, 0)),
#             (re.compile(r'.*表$'), ('simhei.ttf', 50, 1)),
#             (re.compile(r'.*单位.*'), ('simfang.ttf', 36, 0)),
#             (re.compile(r'.*[其项合总年][中目计前].*'), ('simfang.ttf', 40, 1)),
#             (re.compile(r'.*〇'), ('static/fonts/shouxie.ttf', 60, 0)),
#             ]
#
# CELL_MAP = [(lambda box: (box[2] - box[0]) / (box[3] - box[1]) > 20,  # 长格
#              lambda img: img.convert('L').point(
#                  lambda x: 0 if x < 100 else 150))]


# def fstable2image(t, font_size=40, line_pad=-5, keep_ratio=True, font_map=None,
#                   cell_map=None, seal_map=False, vrules='ALL', hrules='ALL'):
#     """ 财务报表专用表格转图片
#     # font_size  正文字号
#     # line_pad   行间距
#     # keep_ratio 是否保持纸张的比例
#     # font_map   字体映射规则集
#     # cell_map   单元格风格映射
#     # seal_map   使用印章映射
#     # vrules     竖线显示规则 'ALL' 全部显示 None 不显示
#     # hrules     横线显示规则 'ALL' 全部显示 None 不显示
#     """
#     if keep_ratio:
#         lines = t.splitlines()
#         w = _len(lines[0]) * font_size // 2
#         h = len(lines) * (font_size + line_pad)
#         if h > w:
#             paper = Paper(direction='v')
#         else:
#             paper = Paper(direction='h')
#         background = paper.image
#         bg_box = paper.box
#     else:
#         background = None
#         bg_box = None
#
#     data = table2image(t, font_size=font_size, line_pad=line_pad,
#                        background=background, bg_box=bg_box,
#                        keep_ratio=keep_ratio, vrules=vrules, hrules=hrules)


#
# for k,v in config.items():
#     for vk,vv in v.items():
#         if vv:
#             v[vk] = []
#             for idx,item in enumerate(vv.split()):
#                 if item[0].isdigit():
#                     v[vk].append('  '+item)
#                 elif item[0] == '（':
#                     v[vk].append(' '+item)
#                 else:
#                     v[vk].append(item)
#     config[k] = v
# print(config)

# d = {}
# t = AwesomeTable()
#
# t.add_row(['项目','2021年前三季度（1-9月）','2020年前三季度（1-9月）'])
# for k,v in config['合并资产负债表'].items():
#     if k.endswith('：'):
#         t.add_row([k,'',''])
#
#     if v is not None:
#         for item in v.split():
#             t.add_row(['  '+item,money(),money()])
#
# # 预处理部分
# t.max_width = 20
# t.table_width = 80
# t.align = 'l'
#
# t = set_align(t,1,'c')
# t = set_align(t,2,'c')
# # t = merge(t,0,0,2)
# nt = []
# for line in str(t).splitlines():
#     if line.__contains__('：') and line[2]!=' ':
#         line = '║'+line[1:-1].replace('║',' ')+'║'
#     nt.append(line)
#
# t =  '\n'.join(nt)
#
# header = AwesomeTable()
# header.add_row(['合并资产负债表'])
# header.add_row(['2020年9月30日'])
# header.add_row(['编制单位:中芯国际集成电路制造有限公司']),
# header.add_row(['单位：千元 币种:人民币 审计类型：未经审计'])
# header = del_line(header)
#
# footer = AwesomeTable()
# footer.add_row(['公司负责人：','李小锐〇', '主管会计工作负责人：','李小锐〇',' 会计机构负责人：','李小锐〇'])
# footer = merge(footer,0)
#
# t = vstack([header,t,footer])
# t = set_align(t,0,'l',2)
# t = set_align(t,0,'r',3)


# # 图片生成器
# paper = Paper(color='white')
# width = len(t.splitlines()[0])
# max_lines = int(width/2/(paper.box[2]-paper.box[0])*(paper.box[3]-paper.box[1])/1.8)
# print(max_lines)
#
# for pno,tab in enumerate(paginate(t,40)):
#     print(pno)
#     print(len(tab.splitlines()))
#     paper = Paper(color='white')
#     data = table2image(tab,font_size=40,line_pad=-5,background=paper.image,bg_box=paper.box,keep_ratio=True)
#     # 后处理部分
#     font_map = [(re.compile(r'.*：$'),('simhei.ttf',40,0)),
#                 (re.compile(r'.*表$'),('simhei.ttf',48,0)),
#                 (re.compile(r'.*单位.*'),('simfang.ttf',36,0)),
#                 (re.compile(r'.*[其项合总年][中目计前].*'),('simfang.ttf',40,1)),
#                 (re.compile(r'〇.*'),('../static/fonts/shouxie.ttf',48,0)),
#                 ]
#     cell_map = [
#         (lambda box: (box[2]-box[0])/(box[3]-box[1])>15, lambda img: img.convert('L').point(lambda x:0 if x<100 else 100))
#     ]
#
#     data = apply_font_map(data,font_map,40)
#     data = apply_cell_map(data,cell_map)
#     cv2.imwrite('page%d.jpg'%pno,data['image'])


# class StatementType(Enum):
#     INCOME_STATEMENT = 10    # 利润表
#     CASH_FLOW_STATEMENT = 20   #现金流量表
#     FINANCIAL_POSITION_STATEMENT = 30 #资产负债表
#     STOCKHOLDERS_EQUITY_STATEMENT = 40 #所有者权益变动表
#     CONSOLIDATED_INCOME_STATEMENT = 11 #合并利润表
#     CONSOLIDATED_CASH_FLOW_STATEMENT = 21 #合并现金流量表
#     CONSOLIDATED_FINANCIAL_POSITION_STATEMENT = 31 #合并资产负债表
#
#
#
# class Statement:
#     def __init__(self,company,date):
#         self.company = company
#         self.date = date
#         self.header = "报表名称 报表编号 编制单位 编制日期 计量单位"
#         self.format = "报告式 账户式"
#         self.body = []
#         self.table = AwesomeTable()
#
#     def bulid_table(self):
#         pass
#
#     def show(self):
#         # print(self.table)
#         img = table2image(self.table)['image']
#         cvshow(img)
#         cv2.imwrite('t.jpg',img)
#
#
# class IncomeStatement(Statement):
#     name = '利润表'
#     ref_url = ''
#
#
# class CashFlowStatement(Statement):
#     name = '现金流量表'
#     types = '一般企业 商业银行 保险公司 证券公司'.split()
#     ref_url = 'https://wiki.mbalib.com/wiki/%E3%80%8A%E4%BC%81%E4%B8%9A%E4%BC%9A%E8%AE%A1%E5%87%86%E5%88%99%E7%AC%AC31%E5%8F%B7-%E7%8E%B0%E9%87%91%E6%B5%81%E9%87%8F%E8%A1%A8%E3%80%8B'
#
#
# class FinancialPositionStatement(Statement):
#     name = '资产负债表'
#     desc = """资产负债表一般有表首、正表两部分。
#         其中，表首概括地说明报表名称、编制单位、编制日期、报表编号、货币名称、计量单位等。
#         正表是资产负债表的主体，列示了用以说明企业财务状况的各个项目。
#         资产负债表正表的格式一般有两种：报告式资产负债表和账户式资产负债表。
#         报告式资产负债表是上下结构，上半部列示资产，下半部列示负债所有者权益
#         具体排列形式又有两种：一是按“资产=负债+所有者权益”的原理排列；
#         二是按“资产-负债=所有者权益”的原理排列。
#         账户式资产负债表是左右结构，左边列示资产，右边列示负债和所有者权益。
#         不管采取什么格式，资产各项目的合计等于负债和所有者权益各项目的合计这一等式不变。
#         """
#     header_string = """<table style="width: 100%">
#                     <caption> <b>资产负债表</b>
#                     </caption>
#                     <tbody><tr>
#                     <td colspan="3" style="text-align:right;">会企01表
#                     </td></tr>
#                     <tr>
#                     <td style="width: 30%"> 编制单位：××有限公司
#                     </td><td style="width: 40%; text-align: center;"> 20×8年12月31日
#                     </td><td style="width: 30%; text-align: right;"> 单位：元
#                     </td></tr></tbody></table>"""
#
#     body_string = """<table class="wikitable" style="width:100%; font-size: 100%;">
# <tbody><tr>
# <th>资　　产</th><th>期末余额</th><th>年初余额
# </th><th>负债和所有者权益<br>（或股东权益）</th><th>期末余额</th><th>年初余额
# </th></tr>
# <tr>
# <td><a href="/wiki/%E6%B5%81%E5%8A%A8%E8%B5%84%E4%BA%A7" title="流动资产">流动资产</a>：</td><td></td><td>
# </td><td><a href="/wiki/%E6%B5%81%E5%8A%A8%E8%B4%9F%E5%80%BA" title="流动负债">流动负债</a>：</td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E8%B4%A7%E5%B8%81%E8%B5%84%E9%87%91" title="货币资金">货币资金</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E7%9F%AD%E6%9C%9F%E5%80%9F%E6%AC%BE" title="短期借款">短期借款</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E4%BA%A4%E6%98%93%E6%80%A7%E9%87%91%E8%9E%8D%E8%B5%84%E4%BA%A7" title="交易性金融资产">交易性金融资产</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E4%BA%A4%E6%98%93%E6%80%A7%E9%87%91%E8%9E%8D%E8%B4%9F%E5%80%BA" title="交易性金融负债">交易性金融负债</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%BA%94%E6%94%B6%E7%A5%A8%E6%8D%AE" title="应收票据">应收票据</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E5%BA%94%E4%BB%98%E7%A5%A8%E6%8D%AE" title="应付票据">应付票据</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%BA%94%E6%94%B6%E8%B4%A6%E6%AC%BE" title="应收账款">应收账款</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E5%BA%94%E4%BB%98%E8%B4%A6%E6%AC%BE" title="应付账款">应付账款</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E9%A2%84%E4%BB%98%E6%AC%BE%E9%A1%B9" title="预付款项">预付款项</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E9%A2%84%E6%94%B6%E6%AC%BE%E9%A1%B9" title="预收款项">预收款项</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%BA%94%E6%94%B6%E5%88%A9%E6%81%AF" title="应收利息">应收利息</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E5%BA%94%E4%BB%98%E8%81%8C%E5%B7%A5%E8%96%AA%E9%85%AC" title="应付职工薪酬">应付职工薪酬</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%BA%94%E6%94%B6%E8%82%A1%E5%88%A9" title="应收股利">应收股利</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E5%BA%94%E4%BA%A4%E7%A8%8E%E8%B4%B9" title="应交税费">应交税费</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%85%B6%E4%BB%96%E5%BA%94%E6%94%B6%E6%AC%BE" title="其他应收款">其他应收款</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E5%BA%94%E4%BB%98%E5%88%A9%E6%81%AF" title="应付利息">应付利息</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%AD%98%E8%B4%A7" title="存货">存货</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E5%BA%94%E4%BB%98%E8%82%A1%E5%88%A9" title="应付股利">应付股利</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E4%B8%80%E5%B9%B4%E5%86%85%E5%88%B0%E6%9C%9F%E7%9A%84%E9%9D%9E%E6%B5%81%E5%8A%A8%E8%B5%84%E4%BA%A7" title="一年内到期的非流动资产">一年内到期的非流动资产</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E5%85%B6%E4%BB%96%E5%BA%94%E4%BB%98%E6%AC%BE" title="其他应付款">其他应付款</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%85%B6%E4%BB%96%E6%B5%81%E5%8A%A8%E8%B5%84%E4%BA%A7" title="其他流动资产">其他流动资产</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E4%B8%80%E5%B9%B4%E5%86%85%E5%88%B0%E6%9C%9F%E7%9A%84%E9%9D%9E%E6%B5%81%E5%8A%A8%E8%B4%9F%E5%80%BA" title="一年内到期的非流动负债">一年内到期的非流动负债</a></td><td></td><td>
# </td></tr>
# <tr>
# <td style="text-align:center;"><b><a href="/wiki/%E6%B5%81%E5%8A%A8%E8%B5%84%E4%BA%A7%E5%90%88%E8%AE%A1" title="流动资产合计">流动资产合计</a></b></td><td></td><td>
# </td><td>　<a href="/wiki/%E5%85%B6%E4%BB%96%E6%B5%81%E5%8A%A8%E8%B4%9F%E5%80%BA" title="其他流动负债">其他流动负债</a></td><td></td><td>
# </td></tr>
# <tr>
# <td><a href="/wiki/%E9%9D%9E%E6%B5%81%E5%8A%A8%E8%B5%84%E4%BA%A7" title="非流动资产">非流动资产</a>：</td><td></td><td>
# </td><td style="text-align:center;"><b><a href="/wiki/%E6%B5%81%E5%8A%A8%E8%B4%9F%E5%80%BA%E5%90%88%E8%AE%A1" title="流动负债合计">流动负债合计</a></b></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%8F%AF%E4%BE%9B%E5%87%BA%E5%94%AE%E9%87%91%E8%9E%8D%E8%B5%84%E4%BA%A7" title="可供出售金融资产">可供出售金融资产</a></td><td></td><td>
# </td><td><a href="/wiki/%E9%9D%9E%E6%B5%81%E5%8A%A8%E8%B4%9F%E5%80%BA" title="非流动负债">非流动负债</a>：</td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E6%8C%81%E6%9C%89%E8%87%B3%E5%88%B0%E6%9C%9F%E6%8A%95%E8%B5%84" title="持有至到期投资">持有至到期投资</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E9%95%BF%E6%9C%9F%E5%80%9F%E6%AC%BE" title="长期借款">长期借款</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E9%95%BF%E6%9C%9F%E5%BA%94%E6%94%B6%E6%AC%BE" title="长期应收款">长期应收款</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E5%BA%94%E4%BB%98%E5%80%BA%E5%88%B8" title="应付债券">应付债券</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E9%95%BF%E6%9C%9F%E8%82%A1%E6%9D%83%E6%8A%95%E8%B5%84" title="长期股权投资">长期股权投资</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E9%95%BF%E6%9C%9F%E5%BA%94%E4%BB%98%E6%AC%BE" title="长期应付款">长期应付款</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E6%8A%95%E8%B5%84%E6%80%A7%E6%88%BF%E5%9C%B0%E4%BA%A7" title="投资性房地产">投资性房地产</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E4%B8%93%E9%A1%B9%E5%BA%94%E4%BB%98%E6%AC%BE" title="专项应付款">专项应付款</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%9B%BA%E5%AE%9A%E8%B5%84%E4%BA%A7" title="固定资产">固定资产</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E9%A2%84%E8%AE%A1%E8%B4%9F%E5%80%BA" title="预计负债">预计负债</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%9C%A8%E5%BB%BA%E5%B7%A5%E7%A8%8B" title="在建工程">在建工程</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E9%80%92%E5%BB%B6%E6%89%80%E5%BE%97%E7%A8%8E%E8%B4%9F%E5%80%BA" title="递延所得税负债">递延所得税负债</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%B7%A5%E7%A8%8B%E7%89%A9%E8%B5%84" title="工程物资">工程物资</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E5%85%B6%E4%BB%96%E9%9D%9E%E6%B5%81%E5%8A%A8%E8%B4%9F%E5%80%BA" title="其他非流动负债">其他非流动负债</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%9B%BA%E5%AE%9A%E8%B5%84%E4%BA%A7%E6%B8%85%E7%90%86" title="固定资产清理">固定资产清理</a></td><td></td><td>
# </td><td style="text-align:center;"><b>非流动负债合计</b></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E7%94%9F%E4%BA%A7%E6%80%A7%E7%94%9F%E7%89%A9%E8%B5%84%E4%BA%A7" title="生产性生物资产">生产性生物资产</a></td><td></td><td>
# </td><td style="text-align:center;"><b><a href="/wiki/%E8%B4%9F%E5%80%BA%E5%90%88%E8%AE%A1" title="负债合计">负债合计</a></b></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E6%B2%B9%E6%B0%94%E8%B5%84%E4%BA%A7" title="油气资产">油气资产</a></td><td></td><td>
# </td><td><a href="/wiki/%E6%89%80%E6%9C%89%E8%80%85%E6%9D%83%E7%9B%8A" title="所有者权益">所有者权益</a>（或<a href="/wiki/%E8%82%A1%E4%B8%9C%E6%9D%83%E7%9B%8A" title="股东权益">股东权益</a>）：</td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E6%97%A0%E5%BD%A2%E8%B5%84%E4%BA%A7" title="无形资产">无形资产</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E5%AE%9E%E6%94%B6%E8%B5%84%E6%9C%AC" title="实收资本">实收资本</a>（或<a href="/wiki/%E8%82%A1%E6%9C%AC" title="股本">股本</a>）</td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%BC%80%E5%8F%91%E6%94%AF%E5%87%BA" title="开发支出">开发支出</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E8%B5%84%E6%9C%AC%E5%85%AC%E7%A7%AF" title="资本公积">资本公积</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%95%86%E8%AA%89" title="商誉">商誉</a></td><td></td><td>
# </td><td>　减：<a href="/wiki/%E5%BA%93%E5%AD%98%E8%82%A1" title="库存股">库存股</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E9%95%BF%E6%9C%9F%E5%BE%85%E6%91%8A%E8%B4%B9%E7%94%A8" title="长期待摊费用">长期待摊费用</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E7%9B%88%E4%BD%99%E5%85%AC%E7%A7%AF" title="盈余公积">盈余公积</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E9%80%92%E5%BB%B6%E6%89%80%E5%BE%97%E7%A8%8E%E8%B5%84%E4%BA%A7" title="递延所得税资产">递延所得税资产</a></td><td></td><td>
# </td><td>　<a href="/wiki/%E6%9C%AA%E5%88%86%E9%85%8D%E5%88%A9%E6%B6%A6" title="未分配利润">未分配利润</a></td><td></td><td>
# </td></tr>
# <tr>
# <td>　<a href="/wiki/%E5%85%B6%E4%BB%96%E9%9D%9E%E6%B5%81%E5%8A%A8%E8%B5%84%E4%BA%A7" title="其他非流动资产">其他非流动资产</a></td><td></td><td>
# </td><td style="text-align:center;"><b><a href="/wiki/%E6%89%80%E6%9C%89%E8%80%85%E6%9D%83%E7%9B%8A" title="所有者权益">所有者权益</a>（或<a href="/wiki/%E8%82%A1%E4%B8%9C%E6%9D%83%E7%9B%8A" title="股东权益">股东权益</a>）合计</b></td><td></td><td>
# </td></tr>
# <tr>
# <td style="text-align:center;"><b>非流动资产合计</b></td><td></td><td>
# </td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td style="text-align:center;"><b><a href="/wiki/%E8%B5%84%E4%BA%A7%E6%80%BB%E8%AE%A1" title="资产总计">资产总计</a></b></td><td></td><td>
# </td><td style="text-align:center;"><b>负债和所有者权益（或股东权益）总计</b></td><td></td><td>
# </td></tr></tbody></table>"""
#
#     def __init__(self,company,date,header=None,body=None):
#         Statement.__init__(self,company,date)
#         self.header =[ ['','','','','','会企01表'],
#                     ['编制单位：',self.company,'',self.date,'','单位：元']]
#
#         self.body = pd.read_html(self.body_string)[0]
#         # self.header = from_list(self.header)
#         # self.body = from_dataframe(self.body)
#         self.bulid_table()
#         self.get_keys()
#
#     def get_keys(self):
#         df = self.body
#         keys = df['资 产']
#         print(keys)
#
#     def bulid_table(self):
#         self.table = AwesomeTable()
#         self.table.add_rows(self.header)
#         self.table.add_row(list(self.body.columns))
#         self.table.add_rows([row.tolist() for row in self.body.values])
#         self.table.title = self.name
#         self.table.align = 'l'
#
#     def show(self):
#         print(self.table)
#
#         img = table2image(self.table)['image']
#         cvshow(img)
#
# def color_negative_red(val):
#     color = 'red' if val == '_' else 'black'
#     return 'color: %s' % color
#
# class StockholdersEquityStatement(Statement):
#     name = '所有者权益变动表'
#     ref_url = 'https://wiki.mbalib.com/wiki/%E6%89%80%E6%9C%89%E8%80%85%E6%9D%83%E7%9B%8A%E5%8F%98%E5%8A%A8%E8%A1%A8'
#     wiki_table = """
# <table class="wikitable" style="font-size: 100%; width: 100%;">
# <tbody><tr>
# <th rowspan="2">项目</th><th colspan="6">本年金额</th><th colspan="6">上年金额
# </th></tr>
# <tr>
# <th><a href="/wiki/%E5%AE%9E%E6%94%B6%E8%B5%84%E6%9C%AC" title="实收资本">实收资本</a>（或<a href="/wiki/%E8%82%A1%E6%9C%AC" title="股本">股本</a>）</th><th><a href="/wiki/%E8%B5%84%E6%9C%AC%E5%85%AC%E7%A7%AF" title="资本公积">资本公积</a></th><th>减：<a href="/wiki/%E5%BA%93%E5%AD%98%E8%82%A1" title="库存股">库存股</a></th><th><a href="/wiki/%E7%9B%88%E4%BD%99%E5%85%AC%E7%A7%AF" title="盈余公积">盈余公积</a></th><th><a href="/wiki/%E6%9C%AA%E5%88%86%E9%85%8D%E5%88%A9%E6%B6%A6" title="未分配利润">未分配利润</a></th><th><a href="/wiki/%E6%89%80%E6%9C%89%E8%80%85%E6%9D%83%E7%9B%8A%E5%90%88%E8%AE%A1" title="所有者权益合计">所有者权益合计</a></th><th>实收资本（或股本）</th><th>资本公积</th><th>减：库存股</th><th>盈余公积</th><th>未分配利润</th><th><a href="/wiki/%E6%89%80%E6%9C%89%E8%80%85%E6%9D%83%E7%9B%8A%E5%90%88%E8%AE%A1" title="所有者权益合计">所有者权益合计</a>
# </th></tr>
# <tr>
# <td>一、上年年末余额</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>　　加：<a href="/wiki/%E4%BC%9A%E8%AE%A1%E6%94%BF%E7%AD%96" title="会计政策">会计政策</a>变更</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>　　　　前期差错更正</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>二、本年年初余额</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>三、本年增减变动金额（减少以 - 号填列）</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>（一）<a href="/wiki/%E5%87%80%E5%88%A9%E6%B6%A6" title="净利润">净利润</a></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>（二）直接计入所有者权益的<a href="/w/index.php?title=%E5%88%A9%E5%BE%97&amp;action=edit" class="new" title="利得">利得</a>和损失</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>1.<a href="/wiki/%E5%8F%AF%E4%BE%9B%E5%87%BA%E5%94%AE%E9%87%91%E8%9E%8D%E8%B5%84%E4%BA%A7" title="可供出售金融资产">可供出售金融资产</a><a href="/wiki/%E5%85%AC%E5%85%81%E4%BB%B7%E5%80%BC" title="公允价值">公允价值</a>变动净额</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>2.<a href="/wiki/%E6%9D%83%E7%9B%8A%E6%B3%95" title="权益法">权益法</a>下被投资单位其他所有者权益变动的影响</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>3.与计入所有者权益项目相关的<a href="/wiki/%E6%89%80%E5%BE%97%E7%A8%8E" title="所得税">所得税</a>影响</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>4.其他</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>　上述（一）和（二）小计</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>（三）所有者投入和<a href="/wiki/%E5%87%8F%E5%B0%91%E8%B5%84%E6%9C%AC" title="减少资本">减少资本</a></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>1.所有者<a href="/wiki/%E6%8A%95%E5%85%A5%E8%B5%84%E6%9C%AC" title="投入资本">投入资本</a></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>2.<a href="/wiki/%E8%82%A1%E4%BB%BD%E6%94%AF%E4%BB%98" title="股份支付">股份支付</a>计入所有者权益的金额</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>3.其他</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>（四）<a href="/wiki/%E5%88%A9%E6%B6%A6%E5%88%86%E9%85%8D" title="利润分配">利润分配</a></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>1.提取盈余公积</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>2.对所有者（或股东）的分配</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>3.其他</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>（五）所有者权益内部结转</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>1.资本公积转增资本（或股本）</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>2.盈余公积转增资本（或股本）</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>3.盈余公积弥补亏损</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>4.其他</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# <tr>
# <td>四、本年年末余额</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>
# </td></tr>
# </tbody></table>
#     """
#     template_table = pd.read_html(wiki_table)[0]
#
#     def __init__(self, company, date):
#         super().__init__(company, date)
#         self.bulid_table()
#
#     def get_template_from_html(self):
#         t = pd.read_html(self.wiki_table,index_col=0)[0]
#         # t = t.fillna()
#         # t.index = t.index.str.pad(10)
#         # s = t.style.highlight_null().render()
#         print(t.shape)
#         print(t.index)
#         print(t.columns)
#         t[:] = np.random.randint(1,100000,size=t.shape)
#
#         # t = t.applymap(lambda x: ('%.2f') % x)
#         t = t.applymap(lambda x: format(x,',')) # 设置千分点
#         print(t.head())
#
#         return t
#
#     def bulid_table(self):
#         self.template_table = self.get_template_from_html()
#         self.table = AwesomeTable()
#
#         self.table.add_row(['']+list(x[1] for x in self.template_table.columns))
#         self.table.add_rows([[index] + row.tolist() for index,row in zip(self.template_table.index,self.template_table.values)])
#         self.table.title = self.name
#         self.table.align = 'l'
#         # self.table.max_width = 10
#


# ses = StockholdersEquityStatement(company='xx公司',date='2021年12月16日')
# # ses.get_template_from_html()
# ses.show()
