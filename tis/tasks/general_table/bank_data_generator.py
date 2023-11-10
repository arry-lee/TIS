"""
银行流水生成器
"""
import random
import re
from math import ceil

import cv2
import numpy as np
import pandas as pd
import prettytable
from PIL import Image, ImageDraw, ImageFont
from faker import Faker
from mimesis.schema import Field, Schema
from prettytable import PrettyTable, FRAME
from prettytable.prettytable import _str_block_width

from awesometable.awesometable import (
    H_SYMBOLS,
    V_LINE_PATTERN,
    count_padding,
    replace_chinese_to_dunder,
    vstack,
    AwesomeTable,
)
from postprocessor.logo import bank_list

# label_dir = ''
# keys_dict, values_dict, texts, keys, values = key_value_generator(label_dir)

# def _random_long_sentence():
#     return random.choice(texts)

f = Faker("zh_CN")
_ = Field("zh")


def _rmb_upper(value):
    """
    人民币大写
    传入浮点类型的值返回 unicode 字符串
    """
    map = ["零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"]
    unit = [
        "分",
        "角",
        "元",
        "拾",
        "百",
        "千",
        "万",
        "拾",
        "百",
        "千",
        "亿",
        "拾",
        "百",
        "千",
        "万",
        "拾",
        "百",
        "千",
        "兆",
    ]

    nums = []  # 取出每一位数字，整数用字符方式转换避大数出现误差
    for i in range(len(unit) - 3, -3, -1):
        if value >= 10**i or i < 1:
            nums.append(int(round(value / (10**i), 2)) % 10)

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
        words.append("整")
    return "".join(words)


field_dict = {
    "工作日期": ["日期", "交易日期", "交易时间", "入账日期", "记账日期", "交易日"],
    "账号": ["卡号", "主卡卡号", "账号/卡号", "借记卡卡号"],
    "注释": ["摘要", "交易摘要", "交易种类", "摘要代码", "交易名称", "交易描述", "备注"],
    "钞汇": ["现转"],
    "余额": ["账户余额", "交易余额", "账号余额", "联机余额", "活存账户余额"],
    "应用号": ["产品大类", "存款种类", "产品子类"],
    "网点号": ["网点", "交易网点"],
    "操作员": ["交易柜员", "柜员", "柜员流水号", "授权柜员号", "柜员号"],
    "地区号": ["交易地点"],
    "币种": ["货币"],
    "通知种类": ["发行代码"],
    "发生额": ["交易金额"],
}


def _alias(key):
    return random.choice(field_dict[key] + [key])


class BankDetailProvider:
    """银行流水单据生成器"""

    _banks = bank_list

    def __init__(self):
        self.faker = Faker("zh_CN")

    def __call__(self, *args, **kwargs):
        self.name = self.faker.name()
        self.bank = random.choice(self._banks)
        self.cardnumber = self.faker.credit_card_number()
        self.start = self.faker.date_this_decade()
        self.money = random.randint(10000, 100000)
        nums = _("integer_number", start=10, end=20)

        self.df = pd.DataFrame(
            {
                "工作日期": pd.date_range(self.start, periods=nums, freq="M").strftime(
                    "%Y-%m-%d"
                ),
                "账号": self.cardnumber,
                "应用号": 1,
                "序号": range(1, nums + 1),
                "币种": "RMB",
                "钞汇": "钞",
                "交易代码": np.random.randint(0, 3, nums),
                "注释": np.random.choice(["工资", "ATM转账", "ATM取款", "消费", "现存"], nums),
                "借贷": "借",
                "发生额": [
                    _("float_number", start=-1000, end=1000, precision=2)
                    for i in range(nums)
                ],
                "余额": 0,
                "存期": 0,
                "约转期": "不转存",
                "通知种类": 0,
                "利息": 0,
                "利息税": 0,
                "起息日": self.start,
                "止息日": "2099-12-31",
                "地区号": _("zip_code"),
                "网点号": np.random.randint(1000, 1100, nums),
                "操作员": np.random.randint(10000, 20000, nums),
                "界面": np.random.choice(["ATM交易", "网上银行", "批量业务", "POS交易"], nums),
                # '多行文本':'这是一个很长很长很长很长很长很长很长很长很长很长很长很长的句子',
                # '摘要及明细': [_random_long_sentence() for i in range(nums)],
            }
        )
        self.df["借贷"] = np.where(self.df["发生额"] > 0, "贷", "借")
        left = []
        for i in self.df["发生额"]:
            lf = self.money + i
            left.append(lf)
            self.money = lf
        self.df["余额"] = pd.Series((round(i, 2) for i in left))
        self.df["发生额"] = np.abs(self.df["发生额"])

        return {
            "卡号": self.cardnumber,
            "户名": self.name,
            "银行": self.bank,
            "起始日期": str(self.start),
            "截止日期": self.df["工作日期"][nums - 1],
            "操作地区": self.df["地区号"][0],
            "操作网点": random.randint(1000, 1100),
            "操作柜员": random.randint(10000, 20000),
            "流水明细": self.df,
        }


bank_engine = BankDetailProvider()
bank_detail_generator = Schema(bank_engine)


def from_dataframe(df, max_cols=12, drop=True):
    """此处的方法太脏了，只能与banktable2image结合；耦合太严重了"""
    field_names = list(df.columns)
    if drop is True:
        dropkey = [
            # "摘要及明细",
            "应用号",
            "序号",
            "存期",
            "通知种类",
            "利息税",
            "操作员",
            "界面",
            "起息日",
            "利息",
            "约转期",
            "地区号",
            "止息日",
            "钞汇",
            "币种",
        ]
        for i in range(random.randint(0, len(dropkey))):
            field_names.remove(dropkey.pop())
    ndf = df.loc[:, field_names]
    # 更名
    for fno in range(len(field_names)):
        if field_names[fno] in field_dict.keys():
            field_names[fno] = _alias(field_names[fno])

    table = AwesomeTable()

    table.vrules = prettytable.ALL
    table.hrules = prettytable.ALL
    table.header = False
    table.set_style(15)

    max_cols = min(
        max_cols, random.randint(ceil(len(field_names) / 2), len(field_names) // 2 * 3)
    )  # 太脏了

    if len(field_names) <= max_cols:
        table.add_row(field_names)
        for row in ndf.values:
            table.add_row(row.tolist())
        multi = False
    else:
        multi = True
        r = field_names
        table.add_row(r[:max_cols])
        table.add_row(r[max_cols:] + [" "] * (max_cols - len(r[max_cols:])))
        for rno, row in enumerate(ndf.values, start=1):
            r = row.tolist()
            table.add_row(r[:max_cols])
            table.add_row(r[max_cols:] + [" "] * (max_cols - len(r[max_cols:])))
    return table, multi


def bank_table_generator(bank_detail, max_width=16, align="l"):
    b = PrettyTable(header=False)
    b.set_style(15)
    b.vrules = FRAME

    b.title = bank_detail["银行"] + "账户历史明细清单"
    b.add_row(
        [
            "卡号:" + bank_detail["卡号"],
            "户名:" + bank_detail["户名"],
            "起始日期:" + bank_detail["起始日期"],
            "截止日期:" + bank_detail["截止日期"],
        ]
    )
    c = PrettyTable(header=False)
    c.set_style(15)
    c.vrules = FRAME
    c.add_row(
        [
            "操作地区:" + str(bank_detail["操作地区"]),
            "操作网点:" + str(bank_detail["操作网点"]),
            "操作柜员:" + str(bank_detail["操作柜员"]),
        ]
    )

    table, multi = from_dataframe(bank_detail["流水明细"])
    table.max_width = max_width
    table.align = align
    h = vstack([b, c, table])
    return h, multi


def banktable2image(
    table,
    xy=None,
    font_size=20,
    bgcolor="white",
    background=None,
    bg_box=None,
    font_path="simfang.ttf",
    line_pad=0,
    line_height=None,
    logo_path=None,
    watermark=True,
    dot_line=False,
    multiline=False,
    debug=False,
):
    """
    将银行流水单渲染成图片
    """
    assert font_size % 4 == 0
    origin_lines = str(table).splitlines()
    lines = list(filter(lambda x: "<r" not in x, origin_lines))  # 过滤掉标记

    char_width = font_size // 2  # 西文字符宽度
    half_char_width = char_width // 2

    w = (len(lines[0]) + 1) * char_width  # 图片宽度
    h = (len(lines)) * font_size  # 图片高度

    if line_height is None:
        line_height = font_size + line_pad

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
        x0, y0 = xy or (char_width, char_width)
        if watermark and logo_path:
            try:
                logo = Image.open(logo_path).resize((w // 2, w // 2))
                background.paste(logo, (w // 4, h // 4), mask=logo)
            except FileNotFoundError:
                pass

    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
    titlesize = font_size + 8
    titlefont = ImageFont.truetype(font_path, titlesize, encoding="utf-8")

    boxes = set()  # 多行文字的外框是同一个，需要去重
    text_boxes = []  # 文本框

    is_odd_line = True
    if multiline:
        lines_to_draw = (6, 10)
    else:
        lines_to_draw = (6, 8)
    last = 0
    rno = 0
    max_cols = 0

    for lno, line in enumerate(lines):
        v = lno * line_height + y0
        start = half_char_width + x0
        rowleft = x0
        cells = re.split(V_LINE_PATTERN, line)[1:-1]

        if lno == 1:  # title
            title = cells[0].strip()
            draw.text((w // 2, v), title, font=titlefont, fill="black", anchor="mm")
            titlebox = draw.textbbox((w // 2, v), title, font=titlefont, anchor="mm")
            text_boxes.append([titlebox, "text@" + title])
            if logo_path:
                try:
                    logo = Image.open(logo_path)
                    xy = (
                        titlebox[0] - logo.size[0],
                        titlebox[1] + titlesize // 2 - logo.size[1] // 2,
                    )
                    background.paste(logo, xy, mask=logo)
                except FileNotFoundError:
                    pass
            if debug:
                draw.rectangle(titlebox, outline="green")
            continue

        if lno == 7:
            max_cols = len(cells)
        if lno == 6:
            last = v

        if "═" in line:
            if lno in lines_to_draw:  # 用---虚线
                if dot_line:
                    draw.text((0, v), "-" * (2 * len(line) - 2), fill="black")
                else:
                    draw.line((x0, v) + (w - x0, v), fill="black", width=2)

            if lno > 6:
                if multiline:
                    if is_odd_line:
                        text_boxes.append([[x0, last, w - x0, v], "行-row@%d" % rno])
                        is_odd_line = not is_odd_line
                        if debug:
                            draw.rectangle(
                                (x0, last) + (w - x0, v), outline="red", width=2
                            )
                            draw.text((x0, last), "row@%d" % rno, fill="red")
                        rno += 1
                    else:
                        is_odd_line = not is_odd_line

                else:
                    text_boxes.append([[x0, last, w - x0, v], "行-row@%d" % rno])
                    if debug:
                        draw.rectangle((x0, last) + (w - x0, v), outline="red", width=2)
                        draw.text((x0, last), "row@%d" % rno, fill="red")
                    rno += 1
                last = v
            continue

        # 以下内容将不会包含'═'
        for cno, cell in enumerate(cells):
            ll = sum(_str_block_width(c) + 1 for c in cells[:cno]) + 1
            if cell == "":  #
                start += char_width
                continue
            if "═" not in cell:
                box = draw.textbbox((start, v), cell, font=font, anchor="lm")
                if box[1] != box[3]:  # 非空单元内文字框
                    draw.text((start, v), cell, font=font, fill="black", anchor="lm")
                    lpad, rpad = count_padding(cell)
                    l = box[0] + lpad * char_width
                    striped_cell = cell.strip()
                    # 如果有多个空格分隔,例如无线表格
                    if "  " in striped_cell:
                        lt, rt = l, l
                        for text in re.split("( {2,})", striped_cell):
                            if text.strip():
                                rt = lt + _str_block_width(text) * char_width
                                text_box = (lt, box[1], rt, box[3] - 1)
                                if debug:
                                    draw.rectangle(text_box, outline="green")
                                text_boxes.append([text_box, "text@" + text])
                            else:
                                lt = rt + _str_block_width(text) * char_width
                    else:
                        r = box[2] - rpad * char_width
                        text_box = (l, box[1], r, box[3])
                        if debug:
                            draw.rectangle(text_box, outline="green")
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
                cbox = (left, tt * line_height + y0, right, bb * line_height + y0)
                boxes.add(cbox)
                if not is_odd_line and cell.strip():
                    label = "跨行列格-cell@{rno}-{rno},{cno}-{cno}".format(
                        rno=rno - 1, cno=max_cols + cno
                    )
                    if [cbox, label] not in text_boxes:
                        text_boxes.append([cbox, label])
                    if debug:
                        draw.rectangle(cbox, outline="blue", width=3)
                        draw.text((cbox[0], cbox[1]), label, fill="blue")
            else:
                end = start + (len(cell) + 1) * char_width
                left = start - half_char_width
                right = end - half_char_width
                start = end

    # 找表宽
    l, t, r, b = list(boxes)[0]
    for box in boxes:
        l = min(l, box[0])
        t = min(t, box[1])
        r = max(r, box[2])
        b = max(b, box[3])

    boxes = list(filter(lambda x: not (x[0] == l and x[2] == r), boxes))
    l, t, r, b = boxes[0]
    for box in boxes:
        l = min(l, box[0])
        t = min(t, box[1])
        r = max(r, box[2])
        b = max(b, box[3])
    table = (l, t, r, b)

    if debug:
        draw.rectangle([l, t, r, b], outline="purple")
        draw.text((l, t), "table@0", fill="purple", anchor="ld")

    cols = []
    for box in boxes:
        if box[3] == b:
            col = [box[0], t, box[2], b]
            cols.append(col)

    cols.sort()
    for cno, col in enumerate(cols):
        text_boxes.append([col, "列-column@%d" % cno])  # 最底部的就是列
        if debug:
            draw.rectangle(col, outline="pink")
            draw.text((col[0], col[1]), "col@%d" % cno, fill="pink")

    boxes = [tb[0] for tb in text_boxes]  # 单纯的boxes分不清是行列还是表格和文本
    boxes.append([l, t, r, b])
    points = []
    for box in boxes:
        points.append([box[0], box[1]])
        points.append([box[2], box[1]])
        points.append([box[2], box[3]])
        points.append([box[0], box[3]])

    label = [tb[1] for tb in text_boxes] + ["表-table@1"]

    return {
        "image": cv2.cvtColor(np.array(background, np.uint8), cv2.COLOR_RGB2BGR),
        "boxes": boxes,  # box 和 label是一一对应的
        "label": label,
        "points": points,
    }


def banktable2image(
    table,
    xy=None,
    font_size=20,
    bgcolor="white",
    background=None,
    bg_box=None,
    font_path="simfang.ttf",
    line_pad=0,
    line_height=None,
    logo_path=None,
    watermark=True,
    dot_line=False,
    multiline=False,
    debug=False,
):
    """
    将银行流水单渲染成图片
    """
    assert font_size % 4 == 0
    origin_lines = str(table).splitlines()
    lines = list(filter(lambda x: "<r" not in x, origin_lines))  # 过滤掉标记

    char_width = font_size // 2  # 西文字符宽度
    half_char_width = char_width // 2

    w = (len(lines[0]) + 1) * char_width  # 图片宽度
    h = (len(lines)) * font_size  # 图片高度

    if line_height is None:
        line_height = font_size + line_pad

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
        x0, y0 = xy or (char_width, char_width)
        if watermark and logo_path:
            try:
                logo = Image.open(logo_path).resize((w // 2, w // 2))
                background.paste(logo, (w // 4, h // 4), mask=logo)
            except FileNotFoundError:
                pass

    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
    titlesize = font_size + 8
    titlefont = ImageFont.truetype(font_path, titlesize, encoding="utf-8")

    boxes = set()  # 多行文字的外框是同一个，需要去重
    text_boxes = []  # 文本框

    is_odd_line = True
    if multiline:
        lines_to_draw = (6, 10)
    else:
        lines_to_draw = (6, 8)
    last = 0
    rno = 0
    max_cols = 0

    for lno, line in enumerate(lines):
        v = lno * line_height + y0
        start = half_char_width + x0
        rowleft = x0
        cells = re.split(V_LINE_PATTERN, line)[1:-1]

        if lno == 1:  # title
            title = cells[0].strip()
            draw.text((w // 2, v), title, font=titlefont, fill="black", anchor="mm")
            titlebox = draw.textbbox((w // 2, v), title, font=titlefont, anchor="mm")
            text_boxes.append([titlebox, "text@" + title])
            if logo_path:
                try:
                    logo = Image.open(logo_path)
                    xy = (
                        titlebox[0] - logo.size[0],
                        titlebox[1] + titlesize // 2 - logo.size[1] // 2,
                    )
                    background.paste(logo, xy, mask=logo)
                except FileNotFoundError:
                    pass
            if debug:
                draw.rectangle(titlebox, outline="green")
            continue

        if lno == 7:
            max_cols = len(cells)
        if lno == 6:
            last = v

        if "═" in line:
            if lno in lines_to_draw:  # 用---虚线
                if dot_line:
                    draw.text((0, v), "-" * (2 * len(line) - 2), fill="black")
                else:
                    draw.line((x0, v) + (w - x0, v), fill="black", width=2)

            if lno > 6:
                if multiline:
                    if is_odd_line:
                        text_boxes.append([[x0, last, w - x0, v], "行-row@%d" % rno])
                        is_odd_line = not is_odd_line
                        if debug:
                            draw.rectangle(
                                (x0, last) + (w - x0, v), outline="red", width=2
                            )
                            draw.text((x0, last), "row@%d" % rno, fill="red")
                        rno += 1
                    else:
                        is_odd_line = not is_odd_line

                else:
                    text_boxes.append([[x0, last, w - x0, v], "行-row@%d" % rno])
                    if debug:
                        draw.rectangle((x0, last) + (w - x0, v), outline="red", width=2)
                        draw.text((x0, last), "row@%d" % rno, fill="red")
                    rno += 1
                last = v
            continue

        # 以下内容将不会包含'═'
        for cno, cell in enumerate(cells):
            ll = sum(_str_block_width(c) + 1 for c in cells[:cno]) + 1
            if cell == "":  #
                start += char_width
                continue
            if "═" not in cell:
                box = draw.textbbox((start, v), cell, font=font, anchor="lm")
                if box[1] != box[3]:  # 非空单元内文字框
                    draw.text((start, v), cell, font=font, fill="black", anchor="lm")
                    lpad, rpad = count_padding(cell)
                    l = box[0] + lpad * char_width
                    striped_cell = cell.strip()
                    # 如果有多个空格分隔,例如无线表格
                    if "  " in striped_cell:
                        lt, rt = l, l
                        for text in re.split("( {2,})", striped_cell):
                            if text.strip():
                                rt = lt + _str_block_width(text) * char_width
                                text_box = (lt, box[1], rt, box[3] - 1)
                                if debug:
                                    draw.rectangle(text_box, outline="green")
                                text_boxes.append([text_box, "text@" + text])
                            else:
                                lt = rt + _str_block_width(text) * char_width
                    else:
                        r = box[2] - rpad * char_width
                        text_box = (l, box[1], r, box[3])
                        if debug:
                            draw.rectangle(text_box, outline="green")
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
                cbox = (left, tt * line_height + y0, right, bb * line_height + y0)
                boxes.add(cbox)
                if not is_odd_line and cell.strip():
                    label = "跨行列格-cell@{rno}-{rno},{cno}-{cno}".format(
                        rno=rno - 1, cno=max_cols + cno
                    )
                    if [cbox, label] not in text_boxes:
                        text_boxes.append([cbox, label])
                    if debug:
                        draw.rectangle(cbox, outline="blue", width=3)
                        draw.text((cbox[0], cbox[1]), label, fill="blue")
            else:
                end = start + (len(cell) + 1) * char_width
                left = start - half_char_width
                right = end - half_char_width
                start = end

    # 找表宽
    l, t, r, b = list(boxes)[0]
    for box in boxes:
        l = min(l, box[0])
        t = min(t, box[1])
        r = max(r, box[2])
        b = max(b, box[3])

    boxes = list(filter(lambda x: not (x[0] == l and x[2] == r), boxes))
    l, t, r, b = boxes[0]
    for box in boxes:
        l = min(l, box[0])
        t = min(t, box[1])
        r = max(r, box[2])
        b = max(b, box[3])
    table = (l, t, r, b)

    if debug:
        draw.rectangle([l, t, r, b], outline="purple")
        draw.text((l, t), "table@0", fill="purple", anchor="ld")

    cols = []
    for box in boxes:
        if box[3] == b:
            col = [box[0], t, box[2], b]
            cols.append(col)

    cols.sort()
    for cno, col in enumerate(cols):
        text_boxes.append([col, "列-column@%d" % cno])  # 最底部的就是列
        if debug:
            draw.rectangle(col, outline="pink")
            draw.text((col[0], col[1]), "col@%d" % cno, fill="pink")

    boxes = [tb[0] for tb in text_boxes]  # 单纯的boxes分不清是行列还是表格和文本
    boxes.append([l, t, r, b])
    points = []
    for box in boxes:
        points.append([box[0], box[1]])
        points.append([box[2], box[1]])
        points.append([box[2], box[3]])
        points.append([box[0], box[3]])

    label = [tb[1] for tb in text_boxes] + ["表-table@1"]

    return {
        "image": cv2.cvtColor(np.array(background, np.uint8), cv2.COLOR_RGB2BGR),
        "boxes": boxes,  # box 和 label是一一对应的
        "label": label,
        "points": points,
    }
