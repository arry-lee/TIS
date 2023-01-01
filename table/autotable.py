"""
从txt文件还原表结构，减轻工作量
1. 解析 txt文件
2. 各个文本按y分组,
3. 各个文本按x排序

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
from awesometable.imagedata import Cell
from awesometable.imagedata import ImageData, Table, Text
from awesometable.table2imagedata import table2imagedata


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


def on_same_line(rect1, rect2):
    return rect2.top <= rect1.centery <= rect2.bottom or \
           rect1.top <= rect2.centery <= rect1.bottom


def on_same_column(rect1, rect2):
    return rect2.left <= rect1.centerx <= rect2.right or \
           rect1.left <= rect2.centerx <= rect1.right


def get_left_right(texts):
    return min(t.left for t in texts), max(t.right for t in texts)


def filter_cols(cols, min_width):
    for col in cols:
        if col.width < min_width:
            del col


def gen_mesh(test_file):
    with open(test_file, 'r', encoding='utf-8') as f:
        temp = f.read()
    name, dic = parse_label_file(temp)
    
    texts = parse_texts(dic)
    
    left_min, right_max = get_left_right(texts)
    
    img = Image.open(
        os.path.join("E:/00IT/P/uniform/data/financial_statement/", name))
    imd = ImageData(img, texts)
    
    # 计算字体高度
    fz = []
    for text in dic.get('text'):
        fz.append(text[0][2][1] - text[0][0][1])
    counter = Counter(fz)
    min_uint = counter.most_common(1)[0][0]
    # half = min_uint // 2
    print(min_uint)
    
    imd.texts.sort(key=lambda x: (x.top, x.left))
    d = defaultdict(list)
    # for text in imd.texts:
    #     d[text.top // min_uint * min_uint].append(text)
    for k in d:
        d[k].sort(key=lambda x: x.left)
    
    char = img.width // min_uint
    
    # with open('out.txt', 'w', encoding='utf-8') as of:
    #     for k in sorted(d.keys()):
    #         chars = ['_'] * char
    #         xy = d[k][0].topleft
    #         width = d[k][-1].right - d[k][0].left
    #         height = max(x.height for x in d[k])
    #
    #         imd.paste(Image.new('RGBA', (width, height), (0, 255, 0, 125)), xy)
    #         for t in d[k]:
    #             start = t.left // char
    #             chars[start:start + len(t.text)] = list(t.text)
    #         of.write(''.join(chars))
    #         of.write('\n')
    
    lines = get_lines(imd)
    columns = get_columns(imd)  # 这里的列包含了标题
    
    # 找到最大列数
    cols_max = max(len(line) for line in lines)
    print(cols_max)
    # 正规行
    normal_lines = [line for line in lines if len(line) == cols_max]
    unnormal_lines = [line for line in lines if len(line) < cols_max]
    
    normal_rows = get_normal_rows(normal_lines)
    
    cols = get_normal_cols(columns)
    
    unnormal_rows = get_normal_rows(unnormal_lines)
    # 找到所有的列数最大的行
    for row in normal_rows:
        row.left = left_min
        row.width = right_max - left_min
    
    # 找到所有正常列的对齐方式
    # cols = []
    # for col in zip(*normal_lines):
    #     lmin = min(c.left for c in col)
    #     lmax = max(c.left for c in col)
    #     ldiff = lmax - lmin
    #
    #     rmin = min(c.right for c in col)
    #     rmax = max(c.right for c in col)
    #     rdiff = rmax - rmin
    #
    #     if ldiff <= rdiff:
    #         align = 'l'
    #     else:
    #         align = 'r'
    #     print(align)
    #     top = min(c.top for c in lines[0])
    #     bot = max(c.bottom for c in lines[-1])
    #     col = Rect(lmin, top, rmax - lmin, bot - top)
    #     cols.append(col)
    
    # 列的正则化
    fix_cols_width(cols)
    filter_cols(cols, min_uint)
    
    orign_rows = get_orign_rows(left_min, lines, right_max)
    
    new_rows = get_blank_rows(orign_rows)
    # 整合行
    rows = orign_rows + new_rows
    rows.sort(key=lambda x: x.top)
    
    fix_rows_height(rows)
    # 绘制行
    render_rows(imd, rows)
    # 修正列
    fix_cols_height(cols, rows)
    
    render_cols(imd, cols)
    
    # 生成单元格
    # drawer = ImageDraw.Draw(img)
    # t = Table(gen_cells(cols, rows), outline=(0, 0, 255, 255))
    # t.render(drawer)
    # imd.texts.clear()
    imd.save(name + '.color.jpg')
    # img.save(name + '.mesh.jpg')
    return imd, cols, rows


def fix_cols_width(cols):
    # avg_width = []
    # gaps = [cols[i].left - cols[i - 1].right for i in range(1, len(cols))]
    # for col in cols:
    #     avg_width.append(col.width)
    # # 列宽分组平均
    for i in range(1, len(cols)):
        cols[i - 1].width = cols[i].left - cols[i - 1].left
        # cols[i].left = cols[i - 1].right


def gen_cells(cols: List[Rect], rows: List[Rect]):
    cells = []
    for row in rows:
        for col in cols:
            cell = Cell(col.left, row.top, col.width, row.height,
                        outline=(0, 0, 255, 255),
                        visible=True)
            cells.append(cell)
    return cells


def fix_cols_height(cols, rows):
    for col in cols:
        col.top = rows[0].top
        col.height = rows[-1].bottom - rows[0].top


def render_cols(imd, cols):
    # 绘制列
    for i, col in enumerate(cols):
        col_img = Image.new('RGBA', (col.width, col.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(col_img)
        draw.rectangle((0, 0, col.width, col.height), outline='black', width=3)
        # font = load_font('simfang.ttf', 20)
        draw.text((10, 10), str(i), (255, 0, 0, 255), )
        imd.paste(col_img, (col.left, col.top))


def render_rows(imd, rows):
    for row in rows:
        try:
            row_img = Image.new('RGBA', (row.width, row.height),
                                (random.randint(0, 255), random.randint(0, 255),
                                 random.randint(0, 255), 125))
        except:
            pass
        else:
            imd.paste(row_img, (row.left, row.top))


def fix_rows_height(rows):
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
    # 衔接行
    for i in range(0, len(rows) - 1):
        # rows[i].top = rows[i-1].bottom
        rows[i].height = rows[i + 1].top - rows[i].top
        print(rows[i].height)


def get_blank_rows(rows):
    avg_height = sum(row.height for row in rows) // len(rows)
    # 寻找插入空行
    new_rows = []
    for i in range(1, len(rows)):
        if rows[i].top - rows[i - 1].bottom > avg_height:
            new_row = Rect(rows[i - 1].left, rows[i - 1].bottom,
                           rows[i - 1].width,
                           avg_height)
            new_row.centery = (rows[i - 1].bottom + rows[i].top) // 2
            new_rows.append(new_row)
    return new_rows


def get_orign_rows(left_min, lines, right_max):
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


def get_normal_cols(normal_columns):
    cols = []
    for col in normal_columns:
        x = min(c.left for c in col)
        y = min(c.top for c in col)
        w = max(c.right for c in col) - x
        h = max(c.bottom for c in col) - y
        cols.append(Rect(x, y, w, h))
    return cols


def get_lines(imd):
    vstack = []
    lines = []
    for text in imd.texts:
        if not vstack:
            vstack.append(text)
        else:
            if on_same_line(text, vstack[-1]):
                vstack.append(text)
            else:
                lines.append(vstack.copy())
                vstack.clear()
                vstack.append(text)
    if vstack:
        lines.append(vstack.copy())
    return lines


def get_columns(imd):
    stack = []
    cols = []
    imd.texts.sort(key=lambda x: x.left)
    for text in imd.texts:
        if not stack:
            stack.append(text)
        else:
            if on_same_column(text, stack[-1]):
                stack.append(text)
            else:
                cols.append(stack.copy())
                stack.clear()
                stack.append(text)
    if stack:
        cols.append(stack.copy())
    return cols


def parse_texts(dic):
    texts = []
    for text in dic.get('text'):
        font_size = text[0][2][1] - text[0][0][1]
        
        t = Text(text[0][0], text[1], 'red', 'simfang.ttf', font_size)
        t.height = text[0][2][1] - text[0][0][1]
        t.width = text[0][2][0] - text[0][0][0]
        texts.append(t)
        # imd.paste(Image.new('RGBA', (t.width, t.height), (255, 0, 0, 125)),
        #           text[0][0])
    return texts


def point_in_rect(point, rect):
    return rect.left <= point[0] <= rect.right and rect.top <= point[
        1] <= rect.bottom


def modify_font_size(text):
    """精细调整字体高度"""
    fontsize = text.font_size
    width = text.width
    font = load_font(text.font_path, fontsize)
    w = font.getsize(text.text)[0]
    
    while w>width:
        fontsize-=1
        font = load_font(text.font_path,fontsize)
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


def check_font_path(img,text):
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
        else: # 不在单元格里的单独示出
            text.fill = (0,255,0,255)
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
                
            text.text = '_' * left_padding + text.text + '_' * right_padding
            cell.align = 'lm'
            text.xy = text.xy[0]+5,text.xy[1]-6 # magic number to fix

def get_num_size(texts):
    fz = []
    for text in texts:
        if re.match(r"[0-9,)(]+", text.text):
            fz.append(text.font_size)
    return sum(fz) // len(fz)


def fix_num_size(texts):
    size = get_num_size(texts)
    for text in texts:
        if re.match(r"[0-9,)(-]+", text.text):
            text.font_size = size+3


def fill_cells(cells):
    for cell in cells:
        fill_cell(cell)


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
                _r.append(c[0].text.replace('_', ' '))
            except IndexError:
                _r.append(' ')
        _rows.append(_r[:])
    return AwesomeTable(_rows)

"""
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
print('start')
file = "E:/00IT/P/uniform/data/financial_statement/005191382.txt"
# imd, cols, rows = gen_mesh(file)
# imd.show()

pickle_name = file.split('.')[0] + '.pickle'
if os.path.exists(pickle_name):
    with open(pickle_name, 'rb') as f:
        imd, cols, rows = pickle.load(f)
    imd.images.clear()
    for text in imd.texts:
        modify_font_size(text)
        
    fix_num_size(imd.texts)
    put_text_in_cell(imd.texts, imd.tables[0].cells)
    # imd.texts.clear()
    
    fill_cells(imd.tables[0].cells)
    # for col in imd.tables[0].cols:
    #     fill_col(col)
    # show_label()
    
    
    # at = cells_to_awesometable(imd.tables[0]._rows)
    # print(at)
    # im = table2imagedata(at, line_pad=10)
    # im.show()
    for text in imd.texts:
        text.fill = (0,0,0,255)
        text.text = text.text.replace('_',' ')
    #
    # print(imd.tables[0][0][0].topleft,imd.tables[0][0][-1].topright)
    print(imd.tables[0].top_line)
    # print(imd.tables[0].bottom_line)
    # print(imd.tables[0].left_line)
    # print(imd.tables[0].left)
    # print(imd.tables[0].topleft)
    # imd.tables[0].top_line.fill = (0,0,0,255)
    imd.line(imd.tables[0].topleft,imd.tables[0].topright,2,(0,0,0,255))
    

    imd.background = Image.new('RGBA',imd.background.size,(255,255,255,255))
    # render_rows(imd,rows)
    imd.show()

else:
    imd, cols, rows = gen_mesh(file)
    # imd.show()
    
    img = cv2.imread(file.split('.')[0] + '.jpg', cv2.IMREAD_UNCHANGED)
    rows_show = False
    
    
    def update():
        global img
        img = cv2.imread(file.split('.')[0] + '.jpg', cv2.IMREAD_UNCHANGED)
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
    
    
    def draw_line(event, x, y, flags, param):
        """
        双击选列，单击中选行，选中后中间双击删除，右双击调整边界
    
        :param event:
        :param x:
        :param y:
        :param flags:
        :param param:
        :return:
        """
        global select_one, select_col
        if event == cv2.EVENT_LBUTTONDBLCLK:
            update()
            for text in cols:
                print(text)
                if point_in_rect((x, y), text):
                    pt1 = (text.left, text.top)
                    pt2 = (text.right, text.bottom)
                    cv2.rectangle(img, pt1, pt2, (0, 0, 255, 255), 2)
                    select_one = text
                    select_col = True
                    break
        
        if event == cv2.EVENT_LBUTTONDOWN:
            update()
            for text in rows:
                print(text)
                if point_in_rect((x, y), text):
                    pt1 = (text.left, text.top)
                    pt2 = (text.right, text.bottom)
                    cv2.rectangle(img, pt1, pt2, (0, 0, 255, 255), 2)
                    select_one = text
                    select_col = False
                    break
        
        if event == cv2.EVENT_RBUTTONDBLCLK:
            if select_one and select_col:
                select_one.width = int(x) - select_one.left
                i = cols.index(select_one)
                if i < len(cols) - 1:
                    move = cols[i + 1].right - select_one.right
                    cols[i + 1].left = select_one.right
                    cols[i + 1].width = move
                update()
        
        if event == cv2.EVENT_MBUTTONDBLCLK:
            if select_one:
                if select_col:
                    cols.remove(select_one)
                else:
                    rows.remove(select_one)
            update()
    
    
    cv2.namedWindow('image', cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback('image', draw_line)
    
    while 1:
        cv2.imshow('image', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        elif cv2.waitKey(1) & 0xFF == ord('s'):
            cells = gen_cells(cols, rows)
            table = Table(cells)
            imd.tables = [table]
            with open(pickle_name, 'wb') as f:
                pickle.dump((imd, cols, rows), f)
            break
    cv2.destroyAllWindows()
