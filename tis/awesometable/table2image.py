"""
AwesomeTable 转为图片
"""
import os.path
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .awesometable import (
    H_SYMBOLS,
    V_LINE_PATTERN,
    count_padding,
    replace_chinese_to_dunder,
    str_block_width,
)

ORANGE = (235, 119, 46)
BLUE = (204, 237, 255)
LINE_PAT = re.compile(r"(\n*[╔╠╚].+?[╗╣╝]\n*)")

DEFAULT_FONT_CN = "simfang.ttf"
DEFAULT_FONT_EN = "arial.ttf"


@dataclass
class Font:
    """字体信息"""

    path: str
    size: int


@dataclass
class Text:
    """文字绘制信息"""

    xy: tuple[int, int]
    text: str
    font: Any
    anchor: str = "lt"
    color: Any = "black"
    box: tuple[int, int, int, int] = None


@dataclass
class Line:
    """直线绘制信息"""

    start: tuple[int, int]
    end: tuple[int, int]
    width: int
    color: Any = "black"


@dataclass
class MetaData:
    """保存可以还原图片的信息"""

    image: Any
    boxes: list[list[int, int, int, int]]
    label: list[str]
    points: list[Any]
    text: list[Text]
    line: list[Line]


# 延迟绘制，先保存绘制需要的所有参数
def draw_text(pos, txt, color, font, anchor="lt"):
    """
    将任何锚点的字符串转化成 lt 锚点，并且去除前后空格
    返回 Text 对象以用于延迟绘制
    :param pos: tuple 位置
    :param txt: str 文字
    :param color: tuple|str 颜色
    :param font: ImageFont 字体
    :param anchor: str 锚点
    :return: Text
    """
    img = Image.new("RGB", (pos[0] + 1000, pos[1] + 1000), "white")
    draw = ImageDraw.Draw(img)
    box = draw.textbbox(pos, txt, font, anchor)
    pos = box[0], (box[1] + box[3]) // 2
    anchor = "lm"
    if txt != txt.rstrip():
        txt = txt.rstrip()
        box = draw.textbbox(pos, txt, font, anchor)
        pos = box[2], (box[1] + box[3]) // 2
        anchor = "rm"
    if txt != txt.lstrip():
        txt = txt.lstrip()
        box = draw.textbbox(pos, txt, font, anchor)
        pos = box[0], (box[1] + box[3]) // 2 - font.size // 2
        anchor = "lt"
    del img, draw
    return Text(pos, txt, font, anchor, color, box)


def draw_line(pt1, pt2, color, width):
    """
    返回 Line 对象以用于延迟绘制
    :param pt1: tuple 起点
    :param pt2: tuple 终点
    :param color: tuple|str 颜色
    :param width: int 线宽
    :return: Line
    """
    return Line(pt1, pt2, width, color)


def table2image(
    table, font_size=20, font_path="simfang.ttf", offset=0, line_pad=0, **kwargs
):
    """
    将 awesometable 转化为可渲染数据字典
    :param table: AwesomeTable|str
    :param font_size: int
    :param font_path: str
    :param offset: int 字数偏移
    :param line_pad: int 行距
    :param kwargs:
    :return: dict 标注字典
    """

    assert font_size % 4 == 0
    char_width = font_size // 2  # 西文字符宽度
    half_char_width = char_width // 2

    line_height = kwargs.get("line_height", font_size + line_pad)  # 行高
    align = kwargs.get("align", "lr")

    lines = str(table).splitlines()
    width = (len(lines[0]) + 1) * char_width + char_width * offset * 2  # 图片宽度
    height = len(lines) * line_height  # 图片高度

    pos = kwargs.get("xy", (char_width + char_width * offset, char_width))

    background, (_x0, _y0) = _set_background((width, height), pos, kwargs)
    draw = ImageDraw.Draw(background)
    need_striped, striped_color, underline_color = _set_style(kwargs)

    # 字体设置
    zh_font = ImageFont.truetype(font_path, font_size)
    en_font = ImageFont.truetype("arial.ttf", font_size)
    title_font = ImageFont.truetype("ariblk.ttf", font_size + 10)
    subtitle_font = ImageFont.truetype("ariali.ttf", font_size - 2)
    header_font = ImageFont.truetype("arialbi.ttf", font_size - 4)
    text_font = ImageFont.truetype("arial.ttf", font_size)

    if kwargs.get("lang", "cn") == "cn":
        en_font = title_font = subtitle_font = header_font = text_font = zh_font
        align = None
    # 数据结构
    cell_set = set()  # 多行文字的外框是同一个，需要去重
    box_dict = defaultdict(list)  # 单元格映射到文本内容
    table_list = []  # 记录多表格的表格坐标
    text_list = []
    line_list = []

    table_record = width, height, 0, 0  # 记录表格四极
    pen_y = _y0  # 起始行 y 坐标
    sum_diff = 0  # 累积误差

    # 行号
    title_line_no = kwargs.get("title_line", None)
    subtitle_line_no = kwargs.get("subtitle_line", None)
    info_line_no = kwargs.get("info_line", None)

    header_start_line_no = kwargs.get("header_line", 0)
    i = header_start_line_no
    try:
        while lines[i][0] != "╠":
            i += 1
    except IndexError:
        pass
    header_end_line_no = i

    # 开始逐行绘制
    for lno, line in enumerate(lines):
        # 跳过线行
        if re.match(LINE_PAT, line):
            pen_y += line_height
            continue

        pen_x = half_char_width + _x0  # 记录坐标
        cells = re.split(V_LINE_PATTERN, line)[1:-1]
        # 处理多表中间大段文字，单一表格不会访问
        if not cells:
            text_list.append(
                draw_text((pen_x, pen_y), line, "black", text_font, anchor="lm")
            )
            # 遇到文字说明表格结束，记录并重置
            if table_record != (width, height, 0, 0):
                table_list.append(table_record[:])
                table_record = width, height, 0, 0
            pen_y += line_height
            pen_y += 5  # 增加表格和文本间距
            sum_diff += 5
            continue
        if lno in (title_line_no, subtitle_line_no, info_line_no):
            # 处理标题行
            if title_line_no and lno == title_line_no:
                text_list.append(
                    draw_text(
                        (pen_x, pen_y),
                        cells[0].strip(),
                        "black",
                        title_font,
                        anchor="lm",
                    )
                )

            # 处理副标题行
            elif subtitle_line_no and lno == subtitle_line_no:
                text_list.append(
                    draw_text(
                        (pen_x, pen_y),
                        cells[0].strip(),
                        "black",
                        subtitle_font,
                        anchor="lm",
                    )
                )

            # 处理信息行
            elif info_line_no and lno == info_line_no:
                text_list.append(
                    draw_text(
                        (pen_x, pen_y),
                        cells[0].strip(),
                        "black",
                        subtitle_font,
                        anchor="lm",
                    )
                )
            pen_y += line_height
            continue
        # 需要条纹否
        need_striped = (not need_striped) and (lno > header_end_line_no)
        # 用英文重写,左对齐，右对齐
        if header_start_line_no <= lno < header_end_line_no:
            _font = header_font
            _color = "black"
        else:
            _font = en_font
            _color = "black"
        # 逐个单元格绘制
        for cno, cell in enumerate(cells):
            # 前置单元格总字符宽
            lol = sum(str_block_width(c) + 1 for c in cells[:cno]) + 1

            if "═" in cell or cell == "":
                pen_x += (len(cell) + 1) * char_width
                continue

            # 左中锚点对齐
            box = draw.textbbox((pen_x, pen_y), cell, font=zh_font, anchor="lm")

            # 条纹背景
            if striped_color and need_striped:
                draw.rectangle(
                    (
                        box[0] - char_width,
                        pen_y - char_width + 2,
                        box[2] + char_width,
                        pen_y + char_width - 2,
                    ),
                    fill=striped_color,
                )

            striped_cell = cell.strip()
            if box[1] != box[3]:  # 非空判断
                if "  " in striped_cell:
                    lpad = count_padding(cell)[0]  # 此处统计左右空格数
                    left = box[0] + lpad * char_width
                    right = 0
                    for text in re.split("( {2,})", striped_cell):
                        if not text.isspace():
                            right = left + str_block_width(text) * char_width
                            text_list.append(
                                draw_text((left, box[1]), text.strip(), "black", _font)
                            )
                        else:
                            left = right + str_block_width(text) * char_width
                else:
                    if align == "lr":
                        if lno > header_end_line_no and (cno in (0, len(cells) // 2)):
                            # 处理缩进的逻辑,用全大写字母代表标题
                            if striped_cell.isupper():
                                need_indent = False
                                cell = cell.title()
                            else:
                                need_indent = True

                            if need_indent:
                                bx0 = box[0] + char_width * 2
                                _font = en_font
                            else:
                                bx0 = box[0]
                                _font = header_font

                            text_list.append(
                                draw_text(
                                    (bx0, box[1]),
                                    cell.rstrip(),
                                    _color,
                                    _font,
                                    anchor="lt",
                                )
                            )

                        elif header_start_line_no <= lno <= header_end_line_no:
                            text_list.append(
                                draw_text(
                                    (
                                        box[0] // 2 + box[2] // 2,
                                        box[1] // 2 + box[3] // 2,
                                    ),
                                    cell.strip(),
                                    _color,
                                    _font,
                                    anchor="mm",
                                )
                            )
                        else:
                            text_list.append(
                                draw_text(
                                    (box[2], box[1]),
                                    cell.lstrip(),
                                    _color,
                                    _font,
                                    anchor="rt",
                                )
                            )
                    else:
                        text_list.append(
                            draw_text(
                                (pen_x, pen_y),
                                cell,
                                font=zh_font,
                                color="black",
                                anchor="lm",
                            )
                        )
                    # 如果有多个空格分隔,例如无线表格

            pen_x = box[2] + char_width
            top = lno - 1
            btm = lno + 1
            # 上下查找边框
            while replace_chinese_to_dunder(lines, top)[lol] not in H_SYMBOLS:
                top -= 1
            while replace_chinese_to_dunder(lines, btm)[lol] not in H_SYMBOLS:
                btm += 1

            cell_box = (
                box[0] - half_char_width,
                top * line_height + _y0 + sum_diff,
                box[2] + half_char_width,
                btm * line_height + _y0 + sum_diff,
            )
            cell_set.add(cell_box)
            box_dict[cell_box].append(striped_cell)
            # 记录当前的表格坐标
            table_record = (
                min(table_record[0], cell_box[0]),
                min(table_record[1], cell_box[1]),
                max(table_record[2], cell_box[2]),
                max(table_record[3], cell_box[3]),
            )

            # if header_start_line_no <= lno < header_end_line_no:
            #     line_list.append(draw_line(
            #         (cb[0] + char_width, cb[3]), (cb[2] - char_width, cb[3]),
            #         "black",
            #         width=2,
            #     ))
            # elif underline_color and lno % 7 == 2 and lno > header_end_line_no + 1:
            #     line_list.append(draw_line(
            #         (cb[0] + char_width, cb[1]), (cb[2] - char_width, cb[1]),
            #         underline_color,
            #         width=2,
            #     ))
            #     line_list.append(draw_line(
            #         (cb[0] + char_width, cb[3]), (cb[2] - char_width, cb[3]),
            #         underline_color,
            #         width=2,
            #     ))
        pen_y += line_height

    if table_record != (width, height, 0, 0):
        table_list.append(table_record[:])

    _draw_back_pattern(background, box_dict, kwargs)

    _draw_tables(table_list, line_list, kwargs)

    _draw_cells(cell_set, line_list, kwargs)

    cell_list, label, points = _combine_boxes(text_list, table_list, cell_set)

    render_image(draw, text_list, line_list)

    return {
        "image": cv2.cvtColor(np.array(background, np.uint8), cv2.COLOR_RGB2BGR),
        "boxes": cell_list,
        "label": label,
        "points": points,
        "text": text_list,
        "line": line_list,
    }


def _set_background(size, pos, kwargs):
    # 背景设置
    width, height = size
    _bg = kwargs.get("background", None)
    bg_box = kwargs.get("bg_box", None)
    bg_color = None
    img = None
    if _bg is None:
        bg_color = (255, 255, 255)
    elif isinstance(_bg, str):
        if os.path.exists(_bg):
            img = Image.open(_bg)
        else:
            bg_color = _bg
    elif isinstance(_bg, np.ndarray):
        img = Image.fromarray(cv2.cvtColor(_bg, cv2.COLOR_BGR2RGB))
    elif isinstance(_bg, tuple):
        bg_color = _bg
    elif isinstance(_bg, Image.Image):
        img = _bg
    else:
        raise ValueError(
            "backgound must be path or color or PIL.Image or numpy.ndarray"
        )
    if img and bg_box:
        box_w, box_h = bg_box[2] - bg_box[0], bg_box[3] - bg_box[1]
        img = img.resize(
            (int(img.width * width / box_w), int(img.height * height / box_h))
        )
        pos = int(bg_box[0] * width / box_w), int(bg_box[1] * height / box_h)
    else:
        img = Image.new("RGB", (width, height), bg_color)
    return img, pos


def _set_style(kwargs):
    # 风格选择
    style = kwargs.get("style", None)
    if not style:
        underline_color = None
        striped_color = None
        need_striped = False
    elif style == "striped":
        underline_color = kwargs.get("underline_color", None)
        striped_color = kwargs.get("striped_color", BLUE)
        need_striped = True
    else:
        underline_color = kwargs.get("underline_color", ORANGE)
        striped_color = kwargs.get("striped_color", None)
        need_striped = False
    return need_striped, striped_color, underline_color


def _draw_back_pattern(background, box_dict, kwargs):
    # 处理背景匹配
    back_pattern = kwargs.get("back_pattern", None)
    if back_pattern:
        for box, lst in box_dict.items():
            for i in lst:
                if re.match(back_pattern, i):
                    img = Image.new(
                        "RGBA", (box[2] - box[0], box[3] - box[1]), (50, 50, 50, 100)
                    )
                    background.paste(img, box, mask=img)
                    break


def _draw_tables(table_list, line_list, kwargs):
    border = kwargs.get("border", "tb")
    for tab in table_list:
        if border and "t" in border:
            line_list.append(
                draw_line((tab[0], tab[1]), (tab[2], tab[1]), "black", width=2)
            )
            # line_list.append(draw_line(
            #     (tab[0], tab[1] - 4), (tab[2], tab[1] - 4), "black",
            #     width=2
            # ))
        if border and "b" in border:
            line_list.append(
                draw_line((tab[0], tab[3]), (tab[2], tab[3]), "black", width=2)
            )
            # line_list.append(draw_line(
            #     (tab[0], tab[3] - 4), (tab[2], tab[3] - 4), "black",
            #     width=2
            # ))


def _draw_cells(cell_set, line_list, kwargs):
    vrules = kwargs.get("vrules", "ALL")
    hrules = kwargs.get("hrules", "ALL")
    for box in list(cell_set):
        if vrules == "ALL":
            line_list.append(
                draw_line((box[0], box[1]), (box[0], box[3]), "black", width=2)
            )
            line_list.append(
                draw_line((box[2], box[1]), (box[2], box[3]), "black", width=2)
            )
        if hrules == "ALL":
            line_list.append(
                draw_line((box[0], box[1]), (box[2], box[1]), "black", width=2)
            )
            line_list.append(
                draw_line((box[0], box[3]), (box[2], box[3]), "black", width=2)
            )


def _combine_boxes(text_list, table_boxes, cell_set):
    text_boxes = (
        [[t.box, "text@" + t.text] for t in text_list]
        + [[t, "table@"] for t in table_boxes]
        + [[t, "cell@"] for t in list(cell_set)]
    )
    cell_list = [tb[0] for tb in text_boxes]
    label = [tb[1] for tb in text_boxes]
    points = []
    for cell in cell_list:
        points.extend(
            [
                [cell[0], cell[1]],
                [cell[2], cell[1]],
                [cell[2], cell[3]],
                [cell[0], cell[3]],
            ]
        )
    return cell_list, label, points


def render_image(draw, text_list, line_list):
    """
    渲染文字，直线到图片
    :param draw:
    :param text_list:
    :param line_list:
    :return:
    """
    for text in text_list:
        draw.text(text.xy, text.text, text.color, text.font, text.anchor)
    for line in line_list:
        draw.line(line.start + line.end, line.color, line.width)
    return draw
