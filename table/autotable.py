__doc__ = """
1.文字的ocr自动识别
2.行的自动判断
3.列的初步判断
4.人工删除行，列
5.生成单元格
6.文字归纳到单元格里或外
7.计算单元格里的文字左右填充空格
8.单元格内左对齐
9.文字的字体高度纠正
10.文字的字体（人工识别）
11.文字的颜色自动拾取
12.文字表格的重建
13.awesometable的重建
14.基于table2imagedata的单元格，文字坐标重置
15.线的查找重绘
16.盖章
"""

import os.path
import pickle
import random
import re
from collections import Counter
from collections import defaultdict
from functools import lru_cache
from typing import List

import cv2
from PIL import Image, ImageDraw, ImageFont
from pyrect import Rect

from awesometable.awesometable import AwesomeTable, str_block_width
from awesometable.imagedata import Cell, ImageData, Table
from awesometable.imagedata import Text


@lru_cache
def load_font(font_path, font_size):
    return ImageFont.truetype(font_path, font_size)


def parse_label_file(template_txt):
    """解析标注文件文本"""
    name = ""
    temp_list = template_txt.splitlines(keepends=False)
    pat = re.compile(
        r"(?P<name>.+);(?P<x1>\d+);(?P<y1>\d+);"
        r"(?P<x2>\d+);(?P<y2>\d+);(?P<x3>\d+);"
        r"(?P<y3>\d+);(?P<x4>\d+);(?P<y4>\d+);"
        r"(?P<label>.+)@(?P<content>.*)"
    )
    temp_dict = defaultdict(list)
    for line in temp_list:
        matched = pat.match(line)
        if matched:
            name = matched["name"]
            box = [
                [int(matched["x1"]), int(matched["y1"])],
                [int(matched["x2"]), int(matched["y2"])],
                [int(matched["x3"]), int(matched["y3"])],
                [int(matched["x4"]), int(matched["y4"])],
            ]
            label = matched["label"]
            content = matched["content"]
            if label == "table":
                temp_dict["table"] = [box, content]
            elif label == "row":
                temp_dict["rows"].append(box)
            elif label == "column":
                temp_dict["cols"].append(box)
            elif label == "cell":
                temp_dict["cells"].append(box)
            else:
                temp_dict["text"].append([box, content])
    if not name:
        raise ValueError("Wrong Format Label File!")
    return name, temp_dict


def parse_texts(dic):
    texts = []
    for text in dic.get("text"):
        font_size = text[0][2][1] - text[0][0][1]
        
        t = Text(text[0][0], text[1], "red", "simfang.ttf", font_size)
        t.height = text[0][2][1] - text[0][0][1]
        t.width = text[0][2][0] - text[0][0][0]
        texts.append(t)
        # imd.paste(Image.new('RGBA', (t.width, t.height), (255, 0, 0, 125)),
        #           text[0][0])
    return texts


def in_same_row(rect1, rect2):
    return (
            rect2.top <= rect1.centery <= rect2.bottom
            or rect1.top <= rect2.centery <= rect1.bottom
    )


def in_same_col(rect1, rect2):
    return (
            rect2.left <= rect1.centerx <= rect2.right
            or rect1.left <= rect2.centerx <= rect1.right
    )


def _get_left_right(texts):
    return min(t.left for t in texts), max(t.right for t in texts)


def filter_cols(cols, min_width):
    """过滤列"""
    for col in cols:
        if col.width < min_width:
            del col


def remove_text_from_img(img, texts):
    oimg = img.convert('L').point(lambda x: 0 if x < 50 else 255)
    drawer = ImageDraw.Draw(oimg)
    for text in texts:
        drawer.rectangle((text.left, text.top, text.right, text.bottom), 255)
    return oimg


def get_normal_cols(normal_lines):
    texts = []
    for line in normal_lines:
        for text in line:
            texts.append(text)
    return get_ver_lines(texts)


def strip_lines(lines):
    """移除异常行"""
    pass


def filter_rows(rows, start=0, end=0):
    for i in range(end):
        rows.pop()
    for i in range(start):
        del rows[0]


def get_col_max(lines):
    """计算表格主体的列数
    """
    
    counter = Counter(len(line) for line in lines)
    # 移除掉只出现小于两次的
    # for c in counter:
    #     if counter.get(c)<=2:
    #         del counter[c]
    print(counter)
    cols_max = max(key for key in counter if counter[key] > 2)
    
    # most_common = counter.most_common(1)[0][0] #出现次数最多的
    
    return cols_max


def auto_column_width(cols, left_min, right_max):
    """处理列宽"""
    paddings = []
    for i in range(len(cols)):
        if i == len(cols) - 1:
            right_padding = right_max - cols[i].right
            left_padding = (cols[i].left - cols[i - 1].right) // 2
        elif i == 0:
            left_padding = cols[i].left - left_min
            right_padding = (cols[i + 1].left - cols[i].right) // 2
        
        else:
            left_padding = (cols[i].left - cols[i - 1].right) // 2
            right_padding = (cols[i + 1].left - cols[i].right) // 2
        paddings.append([left_padding, right_padding])
    
    if paddings[1][1] < paddings[1][0]:  # 第一列比较特殊，二分可能不对称
        delta = paddings[1][0] - paddings[1][1]
        paddings[1][0] = paddings[1][1]
        paddings[0][1] += delta
    
    for col, (lp, rp) in zip(cols, paddings):
        col.left -= lp
        col.width += lp + rp
        
        # cols[i - 1].width = left_padding - cols[i - 1].left
        # cols[i].left = cols[i-1].right


def auto_column_height(cols, rows):
    for col in cols:
        col.top = rows[0].top
        col.height = rows[-1].bottom - rows[0].top


def compute_cells(cols: List[Rect], rows: List[Rect]):
    cells = []
    for row in rows:
        for col in cols:
            cell = Cell(
                col.left,
                row.top,
                col.width,
                row.height,
                outline=(0, 0, 255, 255),
                visible=True,
            )
            cells.append(cell)
    return cells


def render_cols(imd, cols):
    # 绘制列
    for i, col in enumerate(cols):
        col_img = Image.new("RGBA", (col.width, col.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(col_img)
        draw.rectangle((0, 0, col.width, col.height), outline=(0, 0, 0, 255),
                       width=3)
        imd.paste(col_img, (col.left, col.top))


def render_rows(imd, rows):
    for row in rows:
        try:
            row_img = Image.new(
                "RGBA",
                (row.width, row.height),
                (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                    125,
                ),
            )
        except:
            pass
        else:
            imd.paste(row_img, (row.left, row.top))


def modify_rows_height(rows):
    for i in range(0, len(rows)):
        if 0 < i < len(rows) - 1:
            top_padding = (rows[i].top - rows[i - 1].bottom) // 2
            bot_padding = (rows[i + 1].top - rows[i].bottom) // 2
        elif i == 0:
            bot_padding = (rows[i + 1].top - rows[i].bottom) // 2
            top_padding = bot_padding
        else:
            top_padding = (rows[i].top - rows[i - 1].bottom) // 2
            bot_padding = top_padding
        rows[i].top -= top_padding
        rows[i].height += top_padding + bot_padding
    # # 衔接行
    # average_height = sum(r.height for r in rows)//len(rows)
    # for i,row in enumerate(rows):
    #     row.height = average_height
    #     if i > 0:
    #         row.top = rows[i-1].bottom
    
    for i in range(0, len(rows) - 1):
        rows[i].height = rows[i + 1].top - rows[i].top


def find_hidden_rows(rows):
    avg_height = sum(row.height for row in rows) // len(rows)
    # 寻找插入空行
    new_rows = []
    for i in range(1, len(rows)):
        if rows[i].top - rows[i - 1].bottom > avg_height:
            new_row = Rect(
                rows[i - 1].left, rows[i - 1].bottom, rows[i - 1].width,
                avg_height
            )
            new_row.centery = (rows[i - 1].bottom + rows[i].top) // 2
            new_rows.append(new_row)
    return new_rows


def get_origin_rows(left_min, lines, right_max):
    rows = []
    for line in lines:
        xy = line[0].topleft
        width = line[-1].right - line[0].left
        height = max(x.height for x in line)
        row = Rect(*xy, width, height)
        rows.append(row)
    for row in rows:
        row.left = left_min
        row.width = right_max - left_min
    return rows


def get_normal_rows(normal_lines):
    rows = []
    for line in normal_lines:
        xy = line[0].topleft
        width = line[-1].right - line[0].left
        height = max(x.height for x in line)
        row = Rect(*xy, width, height)
        rows.append(row)
    return rows


def modify_column_width(normal_columns):
    cols = []
    for i, col in enumerate(normal_columns):
        x = min(c.left for c in col)
        y = min(c.top for c in col)
        w = max(c.right for c in col) - x
        h = max(c.bottom for c in col) - y
        cols.append(Rect(x, y, w, h))
    
    return cols


def get_hor_lines(texts):
    stack = []
    lines = []
    for text in texts:
        if not stack:
            stack.append(text)
        else:
            if in_same_row(text, stack[-1]):
                stack.append(text)
            else:
                lines.append(stack.copy())
                stack.clear()
                stack.append(text)
    if stack:
        lines.append(stack.copy())
    return lines


def get_ver_lines(texts):
    """需要把外部的text去掉"""
    stack = []
    cols = []
    texts.sort(key=lambda x: x.left)
    for text in texts:
        if not stack:
            stack.append(text)
        else:
            if in_same_col(text, stack[-1]):
                stack.append(text)
            else:
                cols.append(stack.copy())
                stack.clear()
                stack.append(text)
    if stack:
        cols.append(stack.copy())
    return cols


def point_in_rect(point, rect):
    return rect.left <= point[0] <= rect.right and \
           rect.top <= point[1] <= rect.bottom


def modify_font_size(text):
    """精细调整字体高度"""
    fontsize = text.font_size
    width = text.width
    font = load_font(text.font_path, fontsize)
    w = font.getsize(text.text)[0]
    
    while w > width:
        fontsize -= 1
        font = load_font(text.font_path, fontsize)
        w = font.getsize(text.text)[0]
    #
    # delta_w = width-w
    # bestfont = "simfang.ttf"
    # print(delta_w, fontsize, text.text)
    #
    # if delta_w>5:
    #
    #     for fontpath in ["simhei.ttf","simkai.ttf"]:
    #         font = load_font(fontpath,fontsize)
    #         w = font.getsize(text.text)[0]
    #         # print(fontpath,abs(width-w),delta_w)
    #         if abs(width-w) < delta_w:
    #             bestfont = fontpath
    #             delta_w = abs(width-w)
    #
    # text.font_path = bestfont
    text.font_size = fontsize


def check_font_path(img, text):
    """自动判断字体高度未处理"""


def put_text_in_cell(texts, cells):
    """
    将text分配到单元格里
    """
    single_texts = []
    for text in texts:
        for cell in cells:
            if point_in_rect(text.center, cell):
                cell.texts.append(text)
                break
        else:  # 不在单元格里的单独示出
            text.fill = (0, 255, 0, 255)
            text.font_path = "simhei.ttf"
            single_texts.append(text)


def fill_cell(cell):
    """补齐所有的cell"""
    if cell.texts:
        text = cell.texts[0]
        left = text.left - cell.left
        right = cell.right - text.right
        # centery = text.centery
        
        w = str_block_width(text.text)
        if w > 0:
            unit = text.width // w
            left_padding = left // unit
            right_padding = right // unit
            # if re.match(r"[0-9,)(]+", text.text):
            #     # text.text = '0' * len(text.text)
            #     text.font_size += 3
            
            text.text = "_" * left_padding + text.text + "_" * right_padding
            cell.align = "lm"
            # text.xy = text.xy[0] + 5, text.xy[1] - 6  # magic number to fix


def fill_cells(cells):
    for cell in cells:
        fill_cell(cell)


def average_digit_font_size(texts):
    fz = []
    for text in texts:
        if re.match(r"[0-9,)(]+", text.text):
            fz.append(text.font_size)
    return sum(fz) // len(fz)


def modify_digit_font_size(texts):
    size = average_digit_font_size(texts)
    for text in texts:
        if re.match(r"[0-9,)(-]+", text.text):
            text.font_size = size + 3


def fill_col(col):
    """同一列的字符宽度相同"""
    # print(col)
    widths = []
    for i, cell in enumerate(col):
        if cell.texts:
            widths.append(str_block_width(cell[0].text))
        # else:
        #     try:
        #         t = col[i-1].texts[0].copy()
        #     except IndexError:
        #         pass
        #     else:
        #         # t.text = ' '
        #         widths.append(str_block_width(t.text))
        #         cell.append(t)
        #         cell.align = 'lm'
    
    counter = Counter(widths)
    ms_width = counter.most_common(1)
    print(ms_width)
    # if ms_width:
    #     w = ms_width[0][0]
    #
    #     for i, cell in enumerate(col):
    #         if cell.texts:
    #             ww = str_block_width(cell[0].text)
    #             if ww<w:
    #                 cell[0].text = cell[0].text + '_'*(w-ww)
    #             if ww>w:
    #                 cell[0].text = cell[0].text[:w-ww]


def cells_to_awesometable(rows):
    _rows = []
    for r in rows:
        _r = []
        for c in r:
            try:
                _r.append(c[0].text.replace("_", " "))
            except IndexError:
                _r.append(" ")
        _rows.append(_r[:])
    return AwesomeTable(_rows)


def get_rows_and_cols_from_label(label_file):
    with open(label_file, "r", encoding="utf-8") as f:
        temp = f.read()
    name, dic = parse_label_file(temp)
    
    texts = parse_texts(dic)
    
    left_min, right_max = _get_left_right(texts)
    
    
    # imd = ImageData(img, texts)
    # 获取无字图片
    # notxt_img = remove_text_from_img(img,texts)
    # notxt_img.show()
    # 计算字体高度
    fz = []
    for text in dic.get("text"):
        fz.append(text[0][2][1] - text[0][0][1])
    counter = Counter(fz)
    min_uint = counter.most_common(1)[0][0]
    # half = min_uint // 2
    print(min_uint)
    
    texts.sort(key=lambda x: (x.top, x.left))
    d = defaultdict(list)
    # for text in texts:
    #     d[text.top // min_uint * min_uint].append(text)
    for k in d:
        d[k].sort(key=lambda x: x.left)
    
    # char = img.width // min_uint
    
    lines = get_hor_lines(texts)
    # columns = get_ver_lines(texts)  # 这里的列包含了标题
    print(lines)
    # 找到最大列数
    cols_max = get_col_max(lines)
    print(cols_max)
    # 正规行
    normal_lines = [line for line in lines if len(line) == cols_max]
    # unnormal_lines = [line for line in lines if len(line) < cols_max]
    
    normal_rows = get_normal_rows(normal_lines)
    # 假设第一个 normal row 为标题栏，
    normal_cols = get_normal_cols(normal_lines)  # 修复了列数不对的bug
    cols = modify_column_width(normal_cols)
    # unnormal_rows = get_normal_rows(unnormal_lines)
    # 找到所有的列数最大的行
    for row in normal_rows:
        row.left = left_min
        row.width = right_max - left_min
    
    # 列的正则化
    auto_column_width(cols, left_min, right_max)
    filter_cols(cols, min_uint)
    
    # strip_lines(lines,cols_max,cols_min=)
    
    orign_rows = get_origin_rows(left_min, lines, right_max)  # 去除首尾的异常行
    
    new_rows = find_hidden_rows(orign_rows)
    # 整合行
    rows = orign_rows + new_rows
    
    filter_rows(rows, start=2, end=1)  # 移除行
    
    rows.sort(key=lambda x: x.top)
    
    modify_rows_height(rows)
    # 绘制行+
    auto_column_height(cols, rows)
    
    # imd.save(name + ".color.jpg")
    # img.save(name + '.mesh.jpg')
    return texts, cols, rows


def get_rows_and_cols_from_pickle(pickle_name):
    with open(pickle_name, "rb") as f:
        texts, cols, rows = pickle.load(f)
    return texts, cols, rows


def rebuild_table(texts, rows, cols):
    """重建表格"""
    cells = compute_cells(cols, rows)
    # imd.images.clear()
    for text in texts:
        modify_font_size(text)
    modify_digit_font_size(texts)
    put_text_in_cell(texts, cells)
    # imd.texts.clear()
    # fill_cells(cells) #这里改变了text内容，仅适用于处理文本

    for text in texts:
        text.fill = (0, 0, 0, 255)
        text.text = text.text.replace("_", " ")
    table = Table(cells)
    return table


def rebuild_imagadata(img, texts, cols, rows):
    """
    处理过的内容
    :param pickle_name:
    :type pickle_name:
    :return:
    :rtype:
    """
    table = rebuild_table(texts, rows, cols)
    
    imd = ImageData(img,texts=texts, tables=[table])
    
    imd.background = Image.new("RGBA", imd.background.size,
                               (255, 255, 255, 255))
    return imd


def get_rows_and_cols_from_file(file):
    # global file, texts, update, scroll_w
    
    pickle_name = file.split(".")[0] + ".pickle"
    if os.path.exists(pickle_name):
         return get_rows_and_cols_from_pickle(pickle_name)
    
    texts, cols, rows = get_rows_and_cols_from_label(file)
    
    def update():
        nonlocal img, cols, rows
        img = cv2.imread(file.split(".")[0] + ".jpg", cv2.IMREAD_UNCHANGED)
        for text in cols:
            pt1 = (text.left, text.top)
            pt2 = (text.right, text.bottom)
            cv2.rectangle(img, pt1, pt2, (255, 0, 0, 125))
        
        for text in rows:
            pt1 = (text.left, text.top)
            pt2 = (text.right, text.bottom)
            cv2.rectangle(img, pt1, pt2, (0, 255, 0, 125))
    
    select_one = None
    select_col = False
    update()
    
    # 鼠标事件
    def mouse(event, x, y, flags, param):
        nonlocal flag, horizontal, vertical, flag_hor, flag_ver, dx, dy, sx, sy, \
          dst, x1, y1, x2, y2, x3, y3, f1, f2
        nonlocal zoom, scroll_har, scroll_var, img_w, img_h, img, win_w, \
          win_h, show_w, show_h
        nonlocal select_one, select_col
        if event == cv2.EVENT_LBUTTONDOWN:  # 左键点击
            if flag == 0:
                if horizontal and 0 < x < win_w and win_h - scroll_w < y < win_h:
                    flag_hor = 1  # 鼠标在水平滚动条上
                elif vertical and win_w - scroll_w < x < win_w and 0 < y < win_h:
                    flag_ver = 1  # 鼠标在垂直滚动条上
                else:
                    update()
                    for text in rows:
                        print(text)
                        if point_in_rect((x + dx, y + dy), text):
                            pt1 = (text.left, text.top)
                            pt2 = (text.right, text.bottom)
                            cv2.rectangle(img, pt1, pt2, (0, 0, 255, 255), 2)
                            select_one = text
                            select_col = False
                            break
                
                if flag_hor or flag_ver:
                    flag = 1  # 进行滚动条垂直
                    x1, y1, x2, y2, x3, y3 = (
                        x,
                        y,
                        dx,
                        dy,
                        sx,
                        sy,
                    )  # 使鼠标移动距离都是相对于初始滚动条点击位置，而不是相对于上一位置
        
        elif event == cv2.EVENT_MOUSEMOVE and (
                flags & cv2.EVENT_FLAG_LBUTTON
        ):  # 按住左键拖曳
            if flag == 1:
                if flag_hor:
                    w = (x - x1) / 2  # 移动宽度
                    dx = x2 + w * f1  # 原图x
                    if dx < 0:  # 位置矫正
                        dx = 0
                    elif dx > img_w - show_w:
                        dx = img_w - show_w
                    sx = x3 + w  # 滚动条x
                    if sx < 0:  # 位置矫正
                        sx = 0
                    elif sx > win_w - scroll_har:
                        sx = win_w - scroll_har
                if flag_ver:
                    h = y - y1  # 移动高度
                    dy = y2 + h * f2  # 原图y
                    if dy < 0:  # 位置矫正
                        dy = 0
                    elif dy > img_h - show_h:
                        dy = img_h - show_h
                    sy = y3 + h  # 滚动条y
                    if sy < 0:  # 位置矫正
                        sy = 0
                    elif sy > win_h - scroll_var:
                        sy = win_h - scroll_var
                dx, dy = int(dx), int(dy)
                img1 = img[dy: dy + show_h, dx: dx + show_w]  # 截取显示图片
                print(dy, dy + show_h, dx, dx + show_w)
                dst = img1.copy()
        elif event == cv2.EVENT_LBUTTONUP:  # 左键释放
            flag, flag_hor, flag_ver = 0, 0, 0
            x1, y1, x2, y2, x3, y3 = 0, 0, 0, 0, 0, 0
        # elif event == cv2.EVENT_MOUSEWHEEL:  # 滚轮
        #     if flags > 0:  # 滚轮上移
        #         zoom += wheel_step
        #         if zoom > 1 + wheel_step * 20:  # 缩放倍数调整
        #             zoom = 1 + wheel_step * 20
        #     else:  # 滚轮下移
        #         zoom -= wheel_step
        #         if zoom < wheel_step:  # 缩放倍数调整
        #             zoom = wheel_step
        #     zoom = round(zoom, 2)  # 取2位有效数字
        #     img_w, img_h = int(img_original_w * zoom), int(img_original_h * zoom)  # 缩放都是相对原图，而非迭代
        #     img_zoom = cv2.resize(img_original, (img_w, img_h), interpolation=cv2.INTER_AREA)
        #     horizontal, vertical = 0, 0
        #     if img_h <= win_h and img_w <= win_w:
        #         dst1 = img_zoom
        #         cv2.resizeWindow("img", img_w, img_h)
        #         scroll_har, scroll_var = 0, 0
        #         f1, f2 = 0, 0
        #     else:
        #         if img_w > win_w and img_h > win_h:
        #             horizontal, vertical = 1, 1
        #             scroll_har, scroll_var = win_w * show_w / img_w, win_h * show_h / img_h
        #             f1, f2 = (img_w - show_w) / (win_w - scroll_har), (img_h - show_h) / (win_h - scroll_var)
        #         elif img_w > win_w and img_h <= win_h:
        #             show_h = img_h
        #             win_h = show_h + scroll_w
        #             scroll_har, scroll_var = win_w * show_w / img_w, 0
        #             f1, f2 = (img_w - show_w) / (win_w - scroll_har), 0
        #         elif img_w <= win_w and img_h > win_h:
        #             show_w = img_w
        #             win_w = show_w + scroll_w
        #             scroll_har, scroll_var = 0, win_h * show_h / img_h
        #             f1, f2 = 0, (img_h - show_h) / (win_h - scroll_var)
        #         dx, dy = dx * zoom, dy * zoom  # 缩放后显示图片相对缩放图片的坐标
        #         sx, sy = dx / img_w * (win_w - scroll_har), dy / img_h * (win_h - scroll_var)
        #         img = img_zoom.copy()  # 令缩放图片为原图
        #         dx, dy = int(dx), int(dy)
        #         img1 = img[dy:dy + show_h, dx:dx + show_w]
        #         dst = img1.copy()
        
        elif event == cv2.EVENT_LBUTTONDBLCLK:
            update()
            for text in cols:
                print(text)
                if point_in_rect((x + dx, y + dy), text):
                    pt1 = (text.left, text.top)
                    pt2 = (text.right, text.bottom)
                    cv2.rectangle(img, pt1, pt2, (0, 0, 255, 255), 2)
                    select_one = text
                    select_col = True
                    break
        
        elif event == cv2.EVENT_RBUTTONDBLCLK:
            if select_one and select_col:
                select_one.width = int(x + dx) - select_one.left
                i = cols.index(select_one)
                if i < len(cols) - 1:
                    move = cols[i + 1].right - select_one.right
                    cols[i + 1].left = select_one.right
                    cols[i + 1].width = move
                update()
        
        elif event == cv2.EVENT_MBUTTONDBLCLK:
            if select_one:
                if select_col:
                    cols.remove(select_one)
                else:
                    rows.remove(select_one)
                    # modify_rows_height(rows)
            update()
        
        if horizontal and vertical:
            sx, sy = int(sx), int(sy)
            # 对dst1画图而非dst，避免鼠标事件不断刷新使显示图片不断进行填充
            dst1 = cv2.copyMakeBorder(
                dst,
                0,
                scroll_w,
                0,
                scroll_w,
                cv2.BORDER_CONSTANT,
                value=[255, 255, 255],
            )
            cv2.rectangle(
                dst1, (sx, show_h), (int(sx + scroll_har), win_h),
                (181, 181, 181), -1
            )  # 画水平滚动条
            cv2.rectangle(
                dst1, (show_w, sy), (win_w, int(sy + scroll_var)),
                (181, 181, 181), -1
            )  # 画垂直滚动条
        elif horizontal == 0 and vertical:
            sx, sy = int(sx), int(sy)
            dst1 = cv2.copyMakeBorder(
                dst, 0, 0, 0, scroll_w, cv2.BORDER_CONSTANT,
                value=[255, 255, 255]
            )
            cv2.rectangle(
                dst1, (show_w, sy), (win_w, int(sy + scroll_var)),
                (181, 181, 181), -1
            )  # 画垂直滚动条
        elif horizontal and vertical == 0:
            sx, sy = int(sx), int(sy)
            dst1 = cv2.copyMakeBorder(
                dst, 0, scroll_w, 0, 0, cv2.BORDER_CONSTANT,
                value=[255, 255, 255]
            )
            cv2.rectangle(
                dst1, (sx, show_h), (int(sx + scroll_har), win_h),
                (181, 181, 181), -1
            )  # 画水平滚动条
        cv2.imshow("img", dst1)
        cv2.waitKey(1)
    
    # 以下是滚动条所需的内容与算法无关
    img_original = cv2.imread(
        file.split(".")[0] + ".jpg", cv2.IMREAD_UNCHANGED
    )  # 此处需换成大于img_w * img_h的图片
    img_original_h, img_original_w = img_original.shape[0:2]  # 原图宽高
    cv2.namedWindow("img", cv2.WINDOW_NORMAL)
    cv2.moveWindow("img", 300, 100)
    img = img_original.copy()
    img_h, img_w = img.shape[0:2]  # 原图宽高
    show_h, show_w = 600, 800  # 显示图片宽高
    horizontal, vertical = 0, 0  # 原图是否超出显示图片
    dx, dy = 0, 0  # 显示图片相对于原图的坐标
    scroll_w = 16  # 滚动条宽度
    sx, sy = 0, 0  # 滚动块相对于滚动条的坐标
    flag, flag_hor, flag_ver = 0, 0, 0  # 鼠标操作类型，鼠标是否在水平滚动条上，鼠标是否在垂直滚动条上
    x1, y1, x2, y2, x3, y3 = 0, 0, 0, 0, 0, 0  # 中间变量
    win_w, win_h = show_w + scroll_w, show_h + scroll_w  # 窗口宽高
    scroll_har, scroll_var = win_w * show_w / img_w, win_h * show_h / img_h  # 滚动条水平垂直长度
    wheel_step, zoom = 0.05, 1  # 缩放系数， 缩放值
    zoom_w, zoom_h = img_w, img_h  # 缩放图宽高
    f1, f2 = (img_w - show_w) / (win_w - scroll_har), (img_h - show_h) / (
            win_h - scroll_var
    )  # 原图可移动部分占滚动条可移动部分的比例
    cv2.resizeWindow("img", win_w, win_h)
    cv2.setMouseCallback("img", mouse)
    # cv2.waitKey()
    while 1:
        if img_h <= show_h and img_w <= show_w:
            cv2.imshow("img", img)
        else:
            if img_w > show_w:
                horizontal = 1
            if img_h > show_h:
                vertical = 1
            i = img[dy: dy + show_h, dx: dx + show_w]
            dst = i.copy()
        
        if cv2.waitKey(1) & 0xFF == ord("s"):
            with open(pickle_name, "wb") as f:
                pickle.dump((texts, cols, rows), f)
            break
    cv2.destroyAllWindows()
    
    return texts, cols, rows


def similar(text):
    out = []
    for i in text:
        if i.isdigit():
            out.append(random.choice('0123456789'))
        else:
            out.append(i)
    return ''.join(out)
    
if __name__ == "__main__":
    label_file =  "E:/00IT/P/uniform/data/financial_statement/005191840.txt"
    texts, cols, rows = get_rows_and_cols_from_file(label_file)
    
    img = Image.open(label_file.split('.')[0]+'.jpg')

    imd = rebuild_imagadata(img,texts,cols,rows)

    # for cell in imd.tables[0]:
    #     cell.outline = (0, 0, 0, 255)
    
    for text in imd.texts:
    
        if re.match(r"[0-9,)(-]+", text.text.strip()):
            text.text = similar(text.text)
            text.underline = True
    imd.line(imd.tables[0].topleft, imd.tables[0].topright, 2, (0, 0, 0, 255))
    imd.show()
    
    print(imd.asdict())
