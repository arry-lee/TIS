"""表格轉換成模板"""
import random
import re

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from prettytable.prettytable import _str_block_width
from pyrect import Rect

from awesometable.awesometable import (
    H_SYMBOLS,
    V_LINE_PATTERN,
    count_padding,
    replace_chinese_to_dunder,
)
from multilang.template import Template, Text
from post_processor.deco import p2c


class FormTemplate(Template):
    """表格类模板"""

    @classmethod
    def from_table(cls, table, **kwargs):
        """从表格字符串生成模板"""
        return table2template(table, **kwargs)

    def replace_text(self, engine, translator=None):
        font = engine.font("n")
        tempfont = ImageFont.truetype(font, self.texts[0].rect.height)
        for text in self.texts:
            if not text.text.isdigit():
                tmp = engine.sentence_fontlike(tempfont, text.rect.width)
                text.text = tmp.title() if random.random() < 0.5 else tmp
            text.font = font

    def render_image_data(self):
        data = super().render_image_data()
        data["image"] = p2c(data["image"])
        return data


def table2template(
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
    fgcolor="black",
):
    """
    将PrettyTable 字符串对象化为模板
    """

    assert font_size % 4 == 0
    lines = str(table).splitlines()
    char_width = font_size // 2
    half_char_width = char_width // 2
    if not xy:
        x, y = 0, 0
    else:
        x, y = xy
    w = (len(lines[0]) + 1) * char_width + x * 2  # 图片宽度
    if line_height is None:
        line_height = font_size + line_pad

    h = (len(lines)) * line_height + y * 2  # 图片高度

    if background is not None and bg_box:
        x1, y1, x2, y2 = bg_box
        w0, h0 = x2 - x1, y2 - y1
        if isinstance(background, str):
            background = Image.open(background)
        elif isinstance(background, np.ndarray):
            background = Image.fromarray(cv2.cvtColor(background, cv2.COLOR_BGR2RGB))
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
        x0, y0 = x + char_width, y + char_width

    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(font_path, font_size, encoding="utf-8")

    cell_boxes = set()  # 多行文字的外框是同一个，需要去重
    text_boxes = []  # 文本框
    texts = []
    for lno, line in enumerate(lines):
        v = lno * line_height + y0
        start = half_char_width + x0

        cells = re.split(V_LINE_PATTERN, line)[1:-1]
        if not cells:
            # text_box = draw.textbbox((start, v), line, font=font, anchor="lm")
            texts.append(
                Text(
                    text=line,
                    rect=Rect(start, v - char_width, font.getlength(line), font_size),
                )
            )
            continue

        for cno, cell in enumerate(cells):
            ll = sum(_str_block_width(c) + 1 for c in cells[:cno]) + 1
            if cell == "" or "═" in cell:
                start += (len(cell) + 1) * char_width
            else:
                box = draw.textbbox((start, v), cell, font=font, anchor="lm")  # 左中对齐
                if box[1] != box[3]:  # 非空单元内文字框
                    # draw.text((start, v), cell, font=font, fill="black", anchor="lm")
                    lpad, rpad = count_padding(cell)
                    l = box[0] + lpad * char_width
                    striped_cell = cell.strip()
                    if "  " in striped_cell:  # 如果有多个空格分隔
                        lt = l
                        rt = 0
                        for text in re.split("( {2,})", striped_cell):
                            if text.strip():
                                rt = lt + _str_block_width(text) * char_width
                                # text_box = (lt, box[1], rt, box[3])
                                # text_boxes.append([text_box, "text@" + text])
                                texts.append(
                                    Text(
                                        text=text,
                                        rect=Rect(
                                            lt,
                                            v - char_width,
                                            font.getlength(text),
                                            font_size,
                                        ),
                                    )
                                )

                            else:  # 此时text是空格
                                lt = rt + _str_block_width(text) * char_width
                    else:
                        r = box[2] - rpad * char_width

                        texts.append(
                            Text(
                                text=striped_cell,
                                rect=Rect(
                                    l,
                                    v - char_width,
                                    font.getlength(striped_cell),
                                    font_size,
                                ),
                            )
                        )

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
                cbox = (left, tt * line_height + y0, right, bb * line_height + y0)
                cell_boxes.add(cbox)

    # 以下处理标注
    for box in cell_boxes:
        text_boxes.append([box, "cell@"])
        if vrules == "ALL":
            draw.line((box[0], box[1]) + (box[0], box[3]), fill=fgcolor, width=2)
            draw.line((box[2], box[1]) + (box[2], box[3]), fill=fgcolor, width=2)
        if hrules == "ALL":
            draw.line((box[0], box[1]) + (box[2], box[1]), fill=fgcolor, width=2)
            draw.line((box[0], box[3]) + (box[2], box[3]), fill=fgcolor, width=2)
        if hrules == "dot":
            draw.text(
                (box[0], box[1]),
                "-" * (int((box[2] - box[0]) / font.getlength("-"))),
                fgcolor,
                font,
                anchor="lm",
            )
            draw.text(
                (box[0], box[3]),
                "-" * (int((box[2] - box[0]) / font.getlength("-"))),
                fgcolor,
                font,
                anchor="lm",
            )

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

    return FormTemplate(background, texts)


def nolinetable2template(
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
    vrules=None,
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
            # draw.text((w // 2, v), title, font=titlefont, fill="black", anchor="mm")
            box = draw.textbbox((w // 2, v), title, font=titlefont, anchor="mm")
            text_boxes.append([box, "text@" + title])

            if logo_path:
                try:
                    logo = Image.open(logo_path)
                    xy = (
                        box[0] - logo.size[0],
                        box[1] + titlesize // 2 - logo.size[1] // 2,
                    )
                    background.paste(logo, xy, mask=logo)
                except FileNotFoundError:
                    pass
            if debug:
                draw.rectangle(box, outline="green")
            continue

        if lno == 7:
            max_cols = len(cells)
        if lno == 6:
            last = v

        if "═" in line:
            if lno in lines_to_draw:  # 用---虚线
                if dot_line and vrules == None:
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
                    # draw.text((start, v), cell, font=font, fill="black", anchor="lm")
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
        text_boxes.append([col, "列-column@%d" % cno])
        if vrules == "all":
            draw.rectangle(col, outline="black")
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

    texts = []
    for lab, box in zip(label, boxes):
        if lab.startswith("text@"):
            texts.append(
                Text(
                    text=lab.removeprefix("text@"),
                    rect=Rect(box[0], box[1], box[2] - box[0], box[3] - box[1]),
                )
            )

    return FormTemplate(background, texts)
