import re

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from prettytable.prettytable import _str_block_width

from awesometable.awesometable import (H_SYMBOLS, V_LINE_PATTERN)


def table2image(
        table,
        xy=None,
        font_size=20,
        bgcolor="white",
        background=None,
        bg_box=None,
        font_path="simfang.ttf",
        line_pad=0,
        line_height=None,
        vrules="ALL",
        hrules="ALL",
        keep_ratio=False,
        debug=False,
):
    """
    将PrettyTable 字符串对象化为表格图片
    """

    assert font_size % 4 == 0
    lines = str(table).splitlines()
    char_width = font_size // 2
    half_char_width = char_width // 2

    w = (len(lines[0]) + 1) * char_width  # 图片宽度
    if line_height is None:
        line_height = font_size + line_pad

    h = (len(lines)) * line_height  # 图片高度

    if background is not None and bg_box:
        x1, y1, x2, y2 = bg_box
        w0, h0 = x2 - x1, y2 - y1
        if isinstance(background, str):
            background = Image.open(background)
        elif isinstance(background, np.ndarray):
            background = Image.fromarray(
                cv2.cvtColor(background, cv2.COLOR_BGR2RGB))
        wb, hb = background.size
        if not keep_ratio:
            wn, hn = int(wb * w / w0), int(hb * h / h0)
            background = background.resize((wn, hn))
            x0, y0 = int(x1 * w / w0), int(y1 * h / h0)
        else:
            wn, hn = int(wb * w / w0), int(hb * w / w0)  # 宽度自适应，高度保持比例
            background = background.resize((wn, hn))
            x0, y0 = int(x1 * w / w0), int(y1 * w / w0)
    else:
        background = Image.new("RGB", (w, h), bgcolor)
        x0, y0 = xy or (char_width, char_width)

    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(font_path, font_size, encoding="utf-8")

    cell_boxes = set()  # 多行文字的外框是同一个，需要去重
    text_boxes = []  # 文本框
    for lno, line in enumerate(lines):
        v = lno * line_height + y0
        start = half_char_width + x0

        cells = re.split(V_LINE_PATTERN, line)[1:-1]
        if not cells:
            draw.text((start, v), line, font=font, fill="black", anchor="lm")
            text_box = draw.textbbox((start, v), line, font=font, anchor="lm")
            text_boxes.append([text_box, "text@" + line])
            continue

        for cno, cell in enumerate(cells):
            ll = sum(
                _str_block_width(c) + 1 for c in cells[:cno]) + 1
            if cell == "" or "═" in cell:
                start += (len(cell) + 1) * char_width
            else:
                box = draw.textbbox((start, v), cell, font=font,
                                    anchor="lm")  # 左中对齐
                if box[1] != box[3]:  # 非空单元内文字框
                    draw.text((start, v), cell, font=font, fill="black",
                              anchor="lm")
                    lpad, rpad = _count_padding(cell)
                    l = box[0] + lpad * char_width
                    striped_cell = cell.strip()
                    if "  " in striped_cell:  # 如果有多个空格分隔
                        lt = l
                        rt = 0
                        for text in re.split("( {2,})", striped_cell):
                            if text.strip():
                                rt = lt + _str_block_width(text) * char_width
                                text_box = (lt, box[1], rt, box[3])
                                text_boxes.append([text_box, "text@" + text])
                                if debug:
                                    draw.rectangle(text_box, outline="green")
                            else:  # 此时text是空格
                                lt = rt + _str_block_width(text) * char_width
                    else:
                        r = box[2] - rpad * char_width
                        text_box = (l, box[1], r, box[3])
                        text_boxes.append([text_box, "text@" + striped_cell])
                        if debug:
                            draw.rectangle(text_box, outline="green")

                left = box[0] - half_char_width  # 其实box以及包括了空白长度，此处可以不偏置
                right = box[2] + half_char_width
                start = right + half_char_width

                # 处理多行文字
                tt = lno - 1
                bb = lno + 1
                # 原因：_str_block_width 和 [ll]不一样,解决方法，将中文替换为2个字母

                while replace_chinese_to_dunder(lines, tt)[ll] not in H_SYMBOLS:
                    tt -= 1
                while replace_chinese_to_dunder(lines, bb)[ll] not in H_SYMBOLS:
                    bb += 1
                cbox = (
                    left, tt * line_height + y0, right, bb * line_height + y0)
                cell_boxes.add(cbox)

    # 以下处理标注
    for box in cell_boxes:
        text_boxes.append([box, "cell@"])
        if vrules == "ALL":
            draw.line((box[0], box[1]) + (box[0], box[3]), fill="black",
                      width=2)
            draw.line((box[2], box[1]) + (box[2], box[3]), fill="black",
                      width=2)
        if hrules == "ALL":
            draw.line((box[0], box[1]) + (box[2], box[1]), fill="black",
                      width=2)
            draw.line((box[0], box[3]) + (box[2], box[3]), fill="black",
                      width=2)
        if debug:
            print(box, "@cell")

    points = []
    boxes = [tb[0] for tb in text_boxes]  # 单纯的boxes分不清是行列还是表格和文本
    l, t, r, b = boxes[0]  # 求表格四极
    for box in boxes:
        points.append([box[0], box[1]])
        points.append([box[2], box[1]])
        points.append([box[2], box[3]])
        points.append([box[0], box[3]])
        l = min(l, box[0])
        t = min(t, box[1])
        r = max(r, box[2])
        b = max(b, box[3])
    boxes.append([l, t, r, b])
    points.append([l, t])
    points.append([r, t])
    points.append([r, b])
    points.append([l, b])

    label = [tb[1] for tb in text_boxes] + ["table@0"]

    return {
        "image" :cv2.cvtColor(np.array(background, np.uint8),
                              cv2.COLOR_RGB2BGR),
        "boxes" :boxes,  # box 和 label是一一对应的
        "label" :label,
        "points":points,
    }


def _count_padding(text):
    lpad, rpad = 0, 0
    for i in text:
        if i == " ":
            lpad += 1
        else:
            break

    for i in text[::-1]:
        if i == " ":
            rpad += 1
        else:
            break
    return lpad, rpad


def replace_chinese_to_dunder(lines, tt):
    l = []
    for x in lines[tt]:
        if _str_block_width(x) == 2:
            l.append("__")
        else:
            l.append(x)
    return "".join(l)
