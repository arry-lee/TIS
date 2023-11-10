"""
将 PrettyTable表格转换ImageData
"""
import re
from collections import defaultdict

from PIL import Image

from awesometable.awesometable import (
    H_LINE_PATTERN,
    H_SYMBOLS,
    V_LINE_PATTERN,
    replace_chinese_to_dunder,
    str_block_width,
)
from awesometable.imagedata import (
    Cell,
    ImageData,
    Table,
    draw_text,
    load_font,
    textbbox,
)


def table2imagedata(
    table,
    xy=None,
    font_size=20,
    bgcolor="white",
    background=None,
    font_path="simfang.ttf",
    line_pad=0,
    line_height=None,
    fgcolor="black",
    bdcolor="black",
    line_width=2,
):
    """
    The table2imagedata function takes a PrettyTable object and returns an ImageData object.
    The ImageData contains the following:
        - A background layer, which is just a white rectangle with black lines on it. The size of the rectangle is determined by the table's dimensions (width x height).
        - A foreground layer, which contains text objects for each cell in the table. These cells are colored based on whether they are part of a merged cell or not.

    :param table: Generate the table image
    :param xy=None: Indicate that the function should draw text from the top left corner of the image
    :param font_size=20: Match the size of chinese characters
    :param bgcolor=&quot;white&quot;: Make the image look better in jupyter notebook
    :param background=None: Create a transparent image
    :param font_path=&quot;simfang.ttf&quot;: Specify the font to be used
    :param line_pad=0: Align the text in the center of each cell
    :param line_height=None: Adjust the line height of each paragraph
    :param fgcolor='black': Set the foreground color of the text
    :param bdcolor='black': Draw the border of cells
    :param line_width=2: Draw the table borders
    :param : Determine the width of each character
    :return: What?
    :doc-author: Trelent
    """
    """
    将PrettyTable 字符串对象化为表格图片
    分层：
    背景层、表格层，文字层
    """

    assert font_size % 4 == 0
    lines = str(table).splitlines()
    char_width = font_size // 2
    half_char_width = char_width // 2

    if line_height is None:
        line_height = font_size + line_pad

    x0, y0 = xy or (char_width, char_width)
    w = (len(lines[0])) * char_width + x0 * 2  # 图片宽度
    h = (len(lines)) * line_height + y0  # 图片高度

    if background is None:
        background = Image.new("RGB", (w, h), bgcolor)

    font = load_font(font_path, font_size)
    cell_boxes = set()  # 多行文字的外框是同一个，需要去重
    texts = []  # 文字写数据
    box_dict = defaultdict(list)  # 单元格映射到文本内容
    cell_text_dict = defaultdict(list)

    table_boxes = []
    table_record = (w, h, 0, 0)

    v = y0
    for lno, line in enumerate(lines):
        if re.match(H_LINE_PATTERN, line):
            continue
        start = half_char_width + x0

        cells = re.split(V_LINE_PATTERN, line)[1:-1]
        if not cells:
            texts.append(
                draw_text(
                    (start, v), line, font_path, font_size, fill=fgcolor, anchor="lm"
                )
            )
            if table_record != (w, h, 0, 0):
                table_boxes.append(table_record[:])
                table_record = (w, h, 0, 0)
                v += line_height
            continue

        for cno, cell in enumerate(cells):
            ll = sum(str_block_width(c) + 1 for c in cells[:cno]) + 1

            if cell == "" or "═" in cell:
                start += (len(cell) + 1) * char_width
                continue

            box = textbbox((start, v), cell, font=font, anchor="lm")  # 左中对齐
            text = draw_text(
                (start, v), cell, font_path, font_size, fill=fgcolor, anchor="lm"
            )
            # text = draw_text(box2rect(box).center, cell.strip(), font_path, font_size, fill=fgcolor,
            #                           anchor="mm")
            if box[1] != box[3]:  # 非空单元内文字框
                texts.append(text)

            left = box[0] - half_char_width
            right = box[2] + half_char_width
            start = right + half_char_width

            tt = lno - 1
            bb = lno + 1
            # 原因：_str_block_width 和 [ll]不一样,解决方法，将中文替换为2个字母
            top = v - line_height // 2 + 2
            bot = v + line_height // 2 + 2
            while replace_chinese_to_dunder(lines, tt)[ll] not in H_SYMBOLS:
                top -= line_height
                tt -= 1
            while replace_chinese_to_dunder(lines, bb)[ll] not in H_SYMBOLS:
                bb += 1
                bot += line_height

            # cbox = (left, tt * line_height + y0, right, bb * line_height + y0)
            cbox = (left, top, right, bot)
            cell_boxes.add(cbox)
            table_record = (
                min(table_record[0], cbox[0]),
                min(table_record[1], cbox[1]),
                max(table_record[2], cbox[2]),
                max(table_record[3], cbox[3]),
            )

            box_dict[cbox].append(cell.strip())
            cell_text_dict[cbox].append(text)
        v += line_height
    if table_record != (w, h, 0, 0):
        table_boxes.append(table_record[:])

    table_cell_dict = defaultdict(list)
    for c in cell_text_dict:
        for t in table_boxes:
            if t[0] <= c[0] and t[1] <= c[1] and t[2] >= c[2] and t[3] >= c[3]:
                table_cell_dict[t].append(c)

    tables = []
    for t in table_cell_dict:
        cells = []
        for box in table_cell_dict[t]:
            cell = Cell(
                box[0],
                box[1],
                box[2] - box[0],
                box[3] - box[1],
                outline=bdcolor,
                line_width=line_width,
            )
            cell.texts = cell_text_dict[box]
            cells.append(cell)
        tables.append(Table(cells))

    return ImageData(background, texts=texts, lines=[], tables=tables, images=[])
