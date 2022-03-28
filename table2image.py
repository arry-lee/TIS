import random
import re
from collections import defaultdict

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from awesometable import H_SYMBOLS, __c, _count_padding, _str_block_width, vpat

ORANGE = (235, 119, 46)
BLUE = (204, 237, 255)
LINE_PAT = re.compile(r"(\n*[╔╠╚].+?[╗╣╝]\n*)")


def table2image(
    table,
    xy=None,
    font_size=20,
    bg_color="white",
    offset=0,  # 字数偏移
    background=None,
    bg_box=None,
    font_path="./static/fonts/simfang.ttf",
    line_pad=0,
    line_height=None,
    vrules="ALL",
    hrules="ALL",
    border="tb",
    debug=False,
    style="striped",
    underline_color=ORANGE,
    striped_color=BLUE,
    bold_pattern=None,
    back_pattern=None,
    align="lr",
    **kwargs
):
    """
    将通用表格渲染成图片、
    双线表、可能有复杂表头、有多行文字、有标题框
    风格：style 可选 striped or simple or other

    """

    assert font_size % 4 == 0

    char_width = font_size // 2  # 西文字符宽度
    half_char_width = char_width // 2
    if line_height is None:
        line_height = font_size + line_pad
    lines = str(table).splitlines()
    w = (len(lines[0]) + 1) * char_width + char_width * offset * 2  # 图片宽度
    h = len(lines) * line_height  # 图片高度

    # 背景设置
    if background is not None and bg_box:
        x1, y1, x2, y2 = bg_box
        w0, h0 = x2 - x1, y2 - y1
        if isinstance(background, str):
            background = Image.open(background)
        elif isinstance(background, np.ndarray):
            background = Image.fromarray(cv2.cvtColor(background, cv2.COLOR_BGR2RGB))
        wb, hb = background.size
        wn, hn = int(wb * w / w0), int(hb * h / h0)
        background = background.resize((wn, hn))
        x0, y0 = int(x1 * w / w0), int(y1 * h / h0)
    else:
        background = Image.new("RGB", (w, h), bg_color)
        x0, y0 = xy or (char_width + char_width * offset, char_width)
    draw = ImageDraw.Draw(background)
    # 风格选择
    if style == "striped":
        underline_color = None
        need_striped = True
    elif style == "simple":
        underline_color = None
        striped_color = None
        need_striped = False
    else:
        striped_color = None
        need_striped = False

    # 字体设置
    font = ImageFont.truetype(font_path, font_size)
    en_font = ImageFont.truetype("arial.ttf", font_size)
    title_font = ImageFont.truetype("ariblk.ttf", font_size + 10)
    subtitle_font = ImageFont.truetype("ariali.ttf", font_size - 2)
    bold_font = ImageFont.truetype("arialbi.ttf", font_size - 4)
    text_font = ImageFont.truetype("arial.ttf", font_size)

    # 数据结构
    cell_boxes = set()  # 多行文字的外框是同一个，需要去重
    text_boxes = []  # 文本框
    box_dict = defaultdict(list)  # 单元格映射到文本内容
    table_boxes = []  # 记录多表格的表格坐标
    lx, ty, rx, by = w, h, 0, 0  # 记录表格四极
    y = y0  # 起始行 y 坐标
    sum_diff = 0  # 累积误差

    # 行号
    TITLE_LINE_NO = kwargs.get("title_line", None)
    SUBTITLE_LINE_NO = kwargs.get("subtitle_line", None)
    INFO_LINE_NO = kwargs.get("info_line", None)
    HEADER_START_LINE_NO = kwargs.get("header_line", 0)
    i = HEADER_START_LINE_NO
    try:
        while lines[i][0] != "╠":
            i += 1
    except:
        pass
    HEADER_END_LINE_NO = i

    # 开始逐行绘制
    for lno, line in enumerate(lines):
        # 跳过线行
        if re.match(LINE_PAT, line):
            y += line_height
            continue

        x = half_char_width + x0  # 记录坐标
        cells = re.split(vpat, line)[1:-1]
        # 处理多表中间大段文字，单一表格不会访问
        if not cells:
            draw.text((x, y), line, "black", text_font, anchor="lm")
            text_box = draw.textbbox((x, y), line, text_font, anchor="lm")
            text_boxes.append([text_box, "text@" + line])
            # 遇到文字说明表格结束，记录并重置
            if (lx, ty, rx, by) != (w, h, 0, 0):
                table_boxes.append([lx, ty, rx, by])
                lx, ty, rx, by = w, h, 0, 0
            y += line_height
            y += 5  # 增加表格和文本间距
            sum_diff += 5
            continue
        # 处理标题行
        if TITLE_LINE_NO and lno == TITLE_LINE_NO:
            text = cells[0].strip()
            draw.text((x, y), text, "black", title_font, anchor="lm")
            bbox = draw.textbbox((x, y), text, title_font, anchor="lm")
            text_boxes.append([bbox, "text@" + text])
            y += line_height
            continue
        # 处理副标题行
        if SUBTITLE_LINE_NO and lno == SUBTITLE_LINE_NO:
            text = cells[0].strip()
            draw.text((x, y), text, "black", subtitle_font, anchor="lm")
            bbox = draw.textbbox((x, y), text, subtitle_font, anchor="lm")
            text_boxes.append([bbox, "text@" + text])
            y += line_height
            continue
        # 处理信息行
        if INFO_LINE_NO and lno == INFO_LINE_NO:
            text = cells[0].strip()
            draw.text((x, y), text, "black", subtitle_font, anchor="lm")
            bbox = draw.textbbox((x, y), text, subtitle_font, anchor="lm")
            text_boxes.append([bbox, "text@" + text])
            y += line_height
            continue

        # 需要条纹否
        need_striped = (not need_striped) and (lno > HEADER_END_LINE_NO)
        need_indent = lno % 7 == 2 and lno > HEADER_END_LINE_NO + 1

        # 用英文重写,左对齐，右对齐
        if HEADER_START_LINE_NO <= lno < HEADER_END_LINE_NO:
            _font = bold_font
            _color = "black"
        elif bold_pattern and need_indent:
            # todo fix this
            _font = bold_font
            _color = underline_color or "black"
        else:
            _font = en_font
            _color = "black"

        for cno, cell in enumerate(cells):
            # 前置单元格总字符宽
            ll = sum(_str_block_width(c) + 1 for c in cells[:cno]) + 1

            if "═" in cell or cell == "":
                x += (len(cell) + 1) * char_width
                continue

            box = draw.textbbox((x, y), cell, font=font, anchor="lm")

            # 条纹背景  # todo fix this
            if striped_color and need_striped:
                draw.rectangle(
                    (
                        box[0] - char_width,
                        y - char_width + 2,
                        box[2] + char_width,
                        y + char_width - 2,
                    ),
                    fill=striped_color,
                )

            striped_cell = cell.strip()
            if box[1] != box[3]:  # 非空判断
                if striped_cell != "ITEM":
                    if align == "lr":
                        if lno>HEADER_END_LINE_NO and (cno == 0 or cno==len(cells)//2):
                            # 处理缩进的逻辑,用全大写字母代表标题
                            if striped_cell.isupper():
                                need_indent = False
                                cell = cell.title()
                            else:
                                need_indent = True

                            if need_indent:
                                b0 = box[0] + char_width * 2
                                _font = en_font
                            else:
                                b0 = box[0]
                                _font = bold_font

                            draw.text(
                                (b0, box[1]), cell.rstrip(), _color, _font, anchor="lt"
                            )
                            _box = draw.textbbox(
                                (b0, box[1]), cell.rstrip(), _font, anchor="lt"
                            )
                            text_box = draw.textbbox(
                                (_box[2], _box[1]), cell.strip(), _font, anchor="rt"
                            )
                        # fix 表头居中对齐
                        elif HEADER_START_LINE_NO<=lno <= HEADER_END_LINE_NO:
                            draw.text(
                                (box[0]//2+box[2]//2, box[1]//2+box[3]//2), cell.strip(), _color, _font,
                                anchor="mm"
                            )
                            text_box = draw.textbbox(
                                (box[0] // 2 + box[2] // 2,box[1] // 2 + box[3] // 2), cell.strip(), _font,
                                anchor="mm"
                            )

                        else:
                            draw.text(
                                (box[2], box[1]),
                                cell.lstrip(),
                                _color,
                                _font,
                                anchor="rt",
                            )
                            _box = draw.textbbox(
                                (box[2], box[1]), cell.lstrip(), _font, anchor="rt"
                            )
                            text_box = draw.textbbox(
                                (_box[0], _box[1]), cell.strip(), _font, anchor="lt"
                            )
                    else:
                        draw.text(
                            (box[0], box[1]), cell.rstrip(), _color, _font, anchor="lt"
                        )
                        _box = draw.textbbox(
                            (box[0], box[1]), cell.rstrip(), _font, anchor="lt"
                        )
                        text_box = draw.textbbox(
                            (_box[2], _box[1]), cell.strip(), _font, anchor="rt"
                        )
                # 此处统计左右空格数
                lpad, rpad = _count_padding(cell)
                l = box[0] + lpad * char_width
                # 如果有多个空格分隔,例如无线表格
                if "  " in striped_cell:
                    lt = l
                    for text in re.split("( {2,})", striped_cell):
                        if text.strip():
                            rt = lt + _str_block_width(text) * char_width
                            text_box = (lt, box[1], rt, box[3] - 1)
                            text_boxes.append([text_box, "text@" + text])
                            if debug:
                                draw.rectangle(text_box, outline="green")
                        else:
                            lt = rt + _str_block_width(text) * char_width
                else:
                    if striped_cell != "-" and striped_cell != "ITEM":
                        text_boxes.append([text_box, "text@" + striped_cell])
                        if debug:
                            draw.rectangle(text_box, outline="green")

            left = box[0] - half_char_width
            right = box[2] + half_char_width
            x = right + half_char_width
            tt = lno - 1
            bb = lno + 1
            # 上下查找边框
            while __c(lines, tt)[ll] not in H_SYMBOLS:
                tt -= 1
            while __c(lines, bb)[ll] not in H_SYMBOLS:
                bb += 1

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
            elif underline_color and lno % 7 == 2 and lno > HEADER_END_LINE_NO + 1:
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
            # issue7 第一个格子里的
            if striped_cell == "ITEM" and cno == 0:  # fixed issue#7
                if random.random() < 0.5:  # 0.5 的概率出现
                    x_ = random.randint(cbox[0], (cbox[2] + cbox[0]) // 2)
                    y_ = random.randint(cbox[1]+half_char_width,(cbox[1] + cbox[3]) // 2)
                    draw.text((x_, y_), striped_cell, _color, _font, anchor="lt")
                    text_box = draw.textbbox((x_, y_), striped_cell, _font, anchor="lt")
                    text_boxes.append([text_box, "text@" + striped_cell])
        y += line_height

    if (lx, ty, rx, by) != (w, h, 0, 0):
        table_boxes.append([lx, ty, rx, by])

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

    # 以下处理标注
    for cbox in table_boxes:
        text_boxes.append([cbox, "table@"])
        if "t" in border:
            draw.line((cbox[0], cbox[1]) + (cbox[2], cbox[1]), fill="black", width=2)
            draw.line(
                (cbox[0], cbox[1] - 4) + (cbox[2], cbox[1] - 4), fill="black", width=2
            )
        if "b" in border:
            draw.line((cbox[0], cbox[3]) + (cbox[2], cbox[3]), fill="black", width=2)
            draw.line(
                (cbox[0], cbox[3] - 4) + (cbox[2], cbox[3] - 4), fill="black", width=2
            )

    cell_boxes = list(cell_boxes)
    for box in cell_boxes:
        text_boxes.append([box, "cell@"])
        if vrules == "ALL":
            draw.line((box[0], box[1]) + (box[0], box[3]), fill="black", width=2)
            draw.line((box[2], box[1]) + (box[2], box[3]), fill="black", width=2)
        if hrules == "ALL":
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
