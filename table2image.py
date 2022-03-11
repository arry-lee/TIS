import random
import re
from collections import defaultdict

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from awesometable import (H_SYMBOLS, __c, _count_padding,
                          _str_block_width, vpat)

ORANGE = (235,119,46)
BLUE = (204,237,255)
LINE_PAT = re.compile(r'(\n*[╔╠╚].+?[╗╣╝]\n*)')
def table2image(table,
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
                border='tb',
                DEBUG=False,
                style = 'striped',
                underline_color=ORANGE,
                striped_color=BLUE,
                bold_pattern=None,
                back_pattern=None,
                align='lr', **kwargs):
    """
    将通用表格渲染成图片、
    双线表、可能有复杂表头、有多行文字、有标题框
    风格：style 可选 striped or simple or other

    """

    assert font_size % 4 == 0  # 图个方便

    char_width = font_size // 2  # 西文字符宽度
    half_char_width = char_width // 2

    if line_height is None:
        line_height = font_size + line_pad

    lines = str(table).splitlines()
    w = (len(lines[0]) + 1) * char_width + char_width * offset * 2  # 图片宽度
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
        wn, hn = int(wb * w / w0), int(hb * h / h0)
        background = background.resize((wn, hn))
        x0, y0 = int(x1 * w / w0), int(y1 * h / h0)
    else:
        background = Image.new('RGB', (w, h), bgcolor)
        x0, y0 = xy or (char_width + char_width * offset, char_width)

    if style=='striped':
        underline_color = None
        need_striped = True
    elif style == 'simple':
        underline_color = None
        striped_color =None
        need_striped = False
    else:
        striped_color = None
        need_striped = False

    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(font_path, font_size)

    en_font = ImageFont.truetype('arial.ttf', font_size)
    title_font = ImageFont.truetype('ariblk.ttf', font_size + 10)
    subtitle_font = ImageFont.truetype('ariali.ttf', font_size - 2)
    bold_font = ImageFont.truetype('arialbi.ttf', font_size-4)
    text_font = ImageFont.truetype('arial.ttf', font_size)

    cell_boxes = set()  # 多行文字的外框是同一个，需要去重
    text_boxes = []  # 文本框
    box_dict = defaultdict(list)  # 单元格映射到文本内容
    table_boxes = []  # 记录多表格的表格坐标
    lx, ty, rx, by = w, h, 0, 0  # 记录表格四极

    v = y0
    sum_diff = 0

    # title_stylesheet = 'no:-1;font:ariblk.ttf;size:30;align:center'
    # title_styledict = {x.split(':') for x in title_stylesheet.split(';')}

    TITLE_LINE_NO = kwargs.get('title_line',None)
    SUBTITLE_LINE_NO = kwargs.get('subtitle_line',None)
    INFO_LINE_NO = kwargs.get('info_line',None)
    HEADER_START_LINE_NO = kwargs.get('header_line',0)

    i = HEADER_START_LINE_NO
    try:
        while lines[i][0] != "╠": i += 1
    except:
        pass
    HEADER_END_LINE_NO = i

    for lno, line in enumerate(lines):
        start = half_char_width + x0
        cells = re.split(vpat, line)[1:-1]

        if re.match(LINE_PAT,line):
            v += line_height
            continue

        if not cells:  # 处理中间大段文字
            draw.text((start, v), line,'black',text_font,anchor='lm')
            text_box = draw.textbbox((start, v), line, text_font,anchor='lm')
            text_boxes.append([text_box, 'text@' + line])

            if (lx, ty, rx, by) != (w, h, 0, 0):
                table_boxes.append([lx, ty, rx, by])
                if DEBUG:
                    draw.rectangle([lx, ty, rx, by], outline='red', width=5)
                lx, ty, rx, by = w, h, 0, 0  # 记录表格坐标
            v += line_height
            v += 5
            sum_diff += 5
            continue

        if TITLE_LINE_NO and lno == TITLE_LINE_NO:
            text = cells[0].strip()
            draw.text((start, v), text,'black',title_font,anchor='lm')
            bbox = draw.textbbox((start, v), text,title_font,anchor='lm')
            text_boxes.append([bbox, 'text@' + text])
            v += line_height
            if DEBUG:
                draw.rectangle(bbox, outline='green')
            continue

        if SUBTITLE_LINE_NO and lno == SUBTITLE_LINE_NO:
            text = cells[0].strip()
            draw.text((start, v), text,'black',subtitle_font,anchor='lm')
            bbox = draw.textbbox((start, v), text, subtitle_font,anchor='lm')
            text_boxes.append([bbox, 'text@' + text])
            v += line_height
            if DEBUG:
                draw.rectangle(bbox, outline='green')
            continue

        if INFO_LINE_NO and lno == INFO_LINE_NO:
            text = cells[0].strip()
            draw.text((start, v), text,'black',subtitle_font,anchor='lm')
            bbox = draw.textbbox((start, v), text, subtitle_font,anchor='lm')
            text_boxes.append([bbox, 'text@' + text])
            v += line_height
            if DEBUG:
                draw.rectangle(bbox, outline='green')
            v += line_height
            continue


        # 以下内容将不会包含'═'
        need_striped = not need_striped
        if lno < HEADER_END_LINE_NO:
            need_striped = False

        for cno, cell in enumerate(cells):
            ll = sum(_str_block_width(c) + 1 for c in cells[:cno]) + 1
            if cell == '':  #
                start += char_width
                continue
            if '═' in cell:
                end = start + (len(cell) + 1) * char_width
                left = start - half_char_width
                right = end - half_char_width
                start = end
                continue

            box = draw.textbbox((start, v), cell, font=font, anchor='lm')

            # 条纹背景
            if striped_color and need_striped:
                draw.rectangle((box[0] - char_width, v-char_width+2,
                                box[2] + char_width, v+char_width-2),
                               fill=striped_color)

            striped_cell = cell.strip()
            if box[1] != box[3]:
                # 用英文重写,左对齐，右对齐
                if HEADER_START_LINE_NO <= lno < HEADER_END_LINE_NO:
                    _font = bold_font
                    _color = 'black'
                elif bold_pattern and lno % 7 == 2 and lno > HEADER_END_LINE_NO + 1:
                    _font = bold_font
                    _color = underline_color or 'black'
                else:
                    _font = en_font
                    _color = 'black'

                if striped_cell != 'ITEM':
                    if align=='lr':
                        if cno == 0:
                            draw.text((box[0], box[1]), cell.rstrip(),_color,_font,anchor='lt')
                            _box = draw.textbbox((box[0], box[1]), cell.rstrip(),_font, anchor='lt')
                            text_box = draw.textbbox((_box[2],_box[1]),cell.strip(),_font,anchor='rt')
                        else:
                            draw.text((box[2], box[1]), cell.lstrip(),_color,_font,anchor='rt')
                            _box = draw.textbbox((box[2], box[1]), cell.lstrip(),_font, anchor='rt')
                            text_box = draw.textbbox((_box[0], _box[1]), cell.strip(),_font, anchor='lt')
                    else:
                        draw.text((box[0], box[1]), cell.rstrip(), _color, _font,anchor='lt')
                        _box = draw.textbbox((box[0], box[1]), cell.rstrip(), _font,anchor='lt')
                        text_box = draw.textbbox((_box[2], _box[1]), cell.strip(),_font, anchor='rt')

                lpad, rpad = _count_padding(cell)
                l = box[0] + lpad * char_width
                # 如果有多个空格分隔,例如无线表格
                if '  ' in striped_cell:
                    lt = l
                    for text in re.split('( {2,})', striped_cell):
                        if text.strip():
                            rt = lt + _str_block_width(text) * char_width
                            text_box = (lt, box[1], rt, box[3] - 1)
                            text_boxes.append([text_box, 'text@' + text])
                            if DEBUG:
                                draw.rectangle(text_box, outline='green')
                        else:
                            lt = rt + _str_block_width(text) * char_width
                else:
                    if striped_cell != '-' and striped_cell != 'ITEM':
                        text_boxes.append([text_box, 'text@' + striped_cell])
                        if DEBUG:
                            draw.rectangle(text_box, outline='green')

            left = box[0] - half_char_width
            right = box[2] + half_char_width
            start = right + half_char_width
            tt = lno - 1
            bb = lno + 1
            # 将中文替换为2个字母
            while __c(lines, tt)[ll] not in H_SYMBOLS: tt -= 1
            while __c(lines, bb)[ll] not in H_SYMBOLS: bb += 1

            cbox = (left, tt * line_height + y0 + sum_diff, right,
                    bb * line_height + y0 + sum_diff)
            cell_boxes.add(cbox)
            margin = char_width
            if HEADER_START_LINE_NO <= lno < HEADER_END_LINE_NO:
                draw.line((cbox[0] + margin, cbox[3]) + (
                    cbox[2] - margin, cbox[3]), fill='black', width=3)
            elif underline_color and lno % 7 == 2 and lno > HEADER_END_LINE_NO + 1:
                draw.line((cbox[0] + margin, cbox[1]) + (
                cbox[2] - margin, cbox[1]), fill=underline_color, width=3)
                draw.line((cbox[0] + margin, cbox[3]) + (
                cbox[2] - margin, cbox[3]), fill=underline_color, width=3)

            # 记录当前的表格坐标
            lx = min(lx, cbox[0])
            ty = min(ty, cbox[1])
            rx = max(rx, cbox[2])
            by = max(by, cbox[3])

            box_dict[cbox].append(striped_cell)
            # issue7 第一个格子里的
            if striped_cell == 'ITEM' and cno == 0:  # fixed issue#7
                if random.random()<0.5: # 0.5 的概率出现
                    x_ = random.randint(cbox[0], (cbox[2] + cbox[0]) // 2)
                    y_pool = [cbox[3]]
                    i = 1
                    while True:
                        if cbox[3] + i * line_height < (cbox[1] + cbox[3]) // 2:
                            y_pool.append(cbox[3] + i * line_height)
                            i += 1
                        else:
                            break
                    y_ = random.choice(y_pool)
                    draw.text((x_, y_), striped_cell, _color, _font,anchor='lb')
                    text_box = draw.textbbox((x_, y_), striped_cell, _font,anchor='lb')
                    text_boxes.append([text_box, 'text@' + striped_cell])
        v += line_height

    if (lx, ty, rx, by) != (w, h, 0, 0):
        table_boxes.append([lx, ty, rx, by])
        if DEBUG:
            draw.rectangle([lx, ty, rx, by], outline='red', width=5)

    # 处理背景匹配
    if back_pattern:
        for box, ls in box_dict.items():
            for s in ls:
                if re.match(back_pattern, s):
                    im = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]),
                                   (50, 50, 50, 100))
                    background.paste(im, box, mask=im)
                    break

    cell_boxes = list(cell_boxes)
    # 以下处理标注
    for cbox in table_boxes:
        text_boxes.append([cbox, 'table@'])
        if 't' in border:
            draw.line((cbox[0], cbox[1]) + (cbox[2], cbox[1]),
                      fill='black', width=2)
            draw.line((cbox[0], cbox[1] - 4) + (cbox[2], cbox[1] - 4),
                      fill='black', width=2)
        if 'b' in border:
            draw.line((cbox[0], cbox[3]) + (cbox[2], cbox[3]),
                      fill='black', width=2)
            draw.line((cbox[0], cbox[3] - 4) + (cbox[2], cbox[3] - 4),
                      fill='black', width=2)

    for box in cell_boxes:
        text_boxes.append([box, 'cell@'])
        if vrules=='ALL':
            draw.line((box[0],box[1])+(box[0],box[3]),fill='black',width=2)
            draw.line((box[2], box[1]) + (box[2], box[3]), fill='black', width=2)
        if hrules=='ALL':
            draw.line((box[0], box[1]) + (box[2], box[1]), fill='black',width=2)
            draw.line((box[0],box[3])+(box[2],box[3]),fill='black',width=2)

    points = []
    cell_boxes = [tb[0] for tb in text_boxes]  # 单纯的boxes分不清是行列还是表格和文本
    label = [tb[1] for tb in text_boxes]
    for box in cell_boxes:
        points.append([box[0], box[1]])
        points.append([box[2], box[1]])
        points.append([box[2], box[3]])
        points.append([box[0], box[3]])
    return {
        'image' :cv2.cvtColor(np.array(background, np.uint8),
                              cv2.COLOR_RGB2BGR),
        'boxes' :cell_boxes,  # box 和 label是一一对应的
        'label' :label,
        'points':points
    }
