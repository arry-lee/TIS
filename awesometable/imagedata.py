"""
1. 利用缓存机制减少字体实例化的次数
2. 利用延迟渲染减少渲染次数，只在实际用到图片的地方渲染图片
3. 各个元素自动标注
4. 各个元素的属性可以自由修改
"""
from collections import defaultdict
from copy import deepcopy
from functools import lru_cache
from typing import List

from PIL import Image, ImageDraw, ImageFont
from pyrect import Rect


# a = list()


class Element(Rect):
    """元素类,同时具有矩的能力，但不是所有的元素都能放东西"""
    
    def __init__(
            self,
            left=0,
            top=0,
            width=0,
            height=0,
            outline=(0, 0, 0, 255),
            line_width=1,
            line_type="s",
            visible=True,
    ):
        super().__init__(left, top, width, height, onChange=self.update)
        self._outline = outline
        self._line_width = line_width
        self.visible = visible
        # 线型
        self._line_fills = [outline] * 4
        self._line_widths = [line_width] * 4
        self._line_types = [line_type] * 4
        
        self._left_line = Line(
            self.topleft,
            self.bottomleft,
            self._line_widths[0],
            self._line_fills[0],
            self._line_types[0],
        )
        self._right_line = Line(
            self.topright,
            self.bottomright,
            self._line_widths[2],
            self._line_fills[2],
            self._line_types[0],
        )
        self._top_line = Line(
            self.topleft,
            self.topright,
            self._line_widths[1],
            self._line_fills[1],
            self._line_types[1],
        )
        self._bottom_line = Line(
            self.bottomleft,
            self.bottomright,
            self._line_widths[3],
            self._line_fills[3],
            self._line_types[3],
        )
        
        self.parent = None #每个元素都有一个直接的父亲

    # 改变的连锁反应是：子元素尺寸改变>本身几何改变>线性更新
    #                         >
    # 本身几何改变>子元素位置改变>线性更新
    
    def update(self,oldbox=None,newbox=None):
        """
        几何状态改变之后会自动更新线
        如果有父类，掉调用父类的更新方法
        # 不能改变子元素的状态，不然就死循环了
        :return:
        :rtype:
        """
        self.update_lines()
        if self.parent:
            self.parent.update()
        
    # ------------- 以下是几何属性 -------
    def update_lines(self, oldbox=None, newbox=None):
        """更新线和重置线是不一样的"""
        self._update_left()
        self._update_right()
        self._update_top()
        self._update_bottom()
    
    def _update_bottom(self):
        self._bottom_line.start = self.bottomleft
        self._bottom_line.end = self.bottomright
        self._bottom_line.fill = self._line_fills[3]
        self._bottom_line.width = self._line_widths[3]
        self._bottom_line.mode = self._line_types[3]
    
    def _update_top(self):
        self._top_line.start = self.topleft
        self._top_line.end = self.topright
        self._top_line.fill = self._line_fills[1]
        self._top_line.width = self._line_widths[1]
        self._top_line.mode = self._line_types[1]
    
    def _update_right(self):
        self._right_line.start = self.topright
        self._right_line.end = self.bottomright
        self._right_line.fill = self._line_fills[2]
        self._right_line.width = self._line_widths[2]
        self._right_line.mode = self._line_types[2]
    
    def _update_left(self):
        self._left_line.start = self.topleft
        self._left_line.end = self.bottomleft
        self._left_line.fill = self._line_fills[0]
        self._left_line.width = self._line_widths[0]
        self._left_line.mode = self._line_types[0]
    
    @property
    def outline(self):
        return self._outline
    
    @outline.setter
    def outline(self, val):
        self._outline = val
        self._line_fills = [val] * 4
        self.update_lines()
    
    @property
    def line_width(self):
        return self._line_width
    
    @line_width.setter
    def line_width(self, val):
        self._line_width = val
        self._line_widths = [val] * 4
        self.update_lines()
    
    @property
    def left_line(self):
        return self._left_line
    
    @left_line.setter
    def left_line(self, val):
        self._line_fills[0] = val[0]
        self._line_widths[0] = val[1]
        self._line_types[0] = val[2]
        self._update_left()
    
    @property
    def top_line(self):
        return self._top_line
    
    @top_line.setter
    def top_line(self, val):
        self._line_fills[1] = val[0]
        self._line_widths[1] = val[1]
        self._line_types[1] = val[2]
        self._update_top()
    
    @property
    def right_line(self):
        return self._right_line
    
    @right_line.setter
    def right_line(self, val):
        self._line_fills[2] = val[0]
        self._line_widths[2] = val[1]
        self._line_types[2] = val[2]
        self._update_right()
    
    @property
    def bottom_line(self):
        return self._bottom_line
    
    @bottom_line.setter
    def bottom_line(self, val):
        self._line_fills[3] = val[0]
        self._line_widths[3] = val[1]
        self._line_types[3] = val[2]
        self._update_bottom()
    
    @property
    def lines(self):
        return self._left_line, self._top_line, self._right_line, self._bottom_line
    
    @property
    def line_widths(self):
        return self._line_widths
    
    @property
    def line_fills(self):
        return self._line_fills
    
    @property
    def line_types(self):
        return self._line_types
    
    def render(self, drawer):
        if self.visible:
            for line in self.lines:
                line.render(drawer)
    
    def __str__(self):
        return "%s(%s,%s,%s,%s)" % (
            self.__class__.__name__,
            self._left,
            self._top,
            self._width,
            self._height,
        )
    
    def show(self):
        im = Image.new(
            "RGBA",
            (self.right + self.line_width, self.bottom + self.line_width),
            (255, 255, 255, 255),
        )
        drawer = ImageDraw.Draw(im)
        self.render(drawer)
        im.crop(
            self.topleft + (
                self.right + self.line_width, self.bottom + self.line_width)
        ).show()


class Box(Element):
    """可以放元素的盒子
    盒子也是一种元素
    盒子里面可以是盒子

    不会纠结于里面东西的排序和大小
    内部元素改变时，自动改变可变的盒子，需要一个字典记录该盒子的父亲
    """
    
    def __init__(self, initlist=None, *args, **kwargs):
        super(Box, self).__init__(*args, **kwargs)
        self.data = []
        if initlist is not None:
            # XXX should this accept an arbitrary sequence?
            if type(initlist) == type(self.data):
                self.data[:] = initlist
            elif isinstance(initlist, Box):
                self.data[:] = initlist.data[:]
            else:
                self.data = list(initlist)
        
            for one in self.data: # 内部元素的父亲
                one.parent = self
    
    def update(self,oldbox=None,newbox=None):
        self.update_data() #里面的方法不会反向传播
        for c in self.data:
            c.update_lines()
        if self.parent:
            self.parent.update()
        self.update_lines() #更新自己线自己的

            
    def update_data(self):
        pass
    
    def __repr__(self):
        return repr(self.data)
    
    # -------- 以下是容器属性
    def __lt__(self, other):
        return self.data < self.__cast(other)
    
    def __le__(self, other):
        return self.data <= self.__cast(other)
    
    def __eq__(self, other):
        return self.data == self.__cast(other)
    
    def __gt__(self, other):
        return self.data > self.__cast(other)
    
    def __ge__(self, other):
        return self.data >= self.__cast(other)
    
    def __cast(self, other):
        return other.data if isinstance(other, Box) else other
    
    def __contains__(self, item):
        return item in self.data
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.__class__(self.data[i])
        else:
            return self.data[i]
    
    def __setitem__(self, i, item):
        self.data[i] = item
    
    def __delitem__(self, i):
        del self.data[i]
    
    def __add__(self, other):
        return self.__copy__().__iadd__(other)
    
    __radd__ = __add__
    
    def __iadd__(self, other):
        if isinstance(other, Box):
            self.data += other.data
        elif isinstance(other, type(self.data)):
            self.data += other
        else:
            self.data += list(other)
        # self.union(other)
        self._left = min(self.left, other.left)
        self._top = min(self.top, other.top)
        self._width = max(self.right, other.right) - self._left
        self._height = max(self.bottom, other.bottom) - self._top
        self.update_lines()
        return self
    
    def __mul__(self, n):
        return self.__class__(self.data * n)
    
    __rmul__ = __mul__
    
    def __imul__(self, n):
        self.data *= n
        return self
    
    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["data"] = deepcopy(self.__dict__["data"])  # 深拷贝
        return inst
    
    def append(self, item):  # item is sub element
        self.data.append(item)
    
    def insert(self, i, item):
        self.data.insert(i, item)
    
    def pop(self, i=-1):
        return self.data.pop(i)
    
    def remove(self, item):
        self.data.remove(item)
    
    def clear(self):
        self.data.clear()
    
    # def copy(self):
    #     return self.__class__(self)
    
    def count(self, item):
        return self.data.count(item)
    
    def index(self, item, *args):
        return self.data.index(item, *args)
    
    def reverse(self):
        self.data.reverse()
    
    def sort(self, /, *args, **kwds):
        self.data.sort(*args, **kwds)
    
    def extend(self, other):
        if isinstance(other, Box):
            self.data.extend(other.data)
        else:
            self.data.extend(other)
    
    # 当盒子移动的时候，内部所有东西都要移动,线也要更新
    def move(self, xOffset, yOffset):
        super().move(xOffset, yOffset)
        for ele in self.data:
            ele.move(xOffset, yOffset)
            ele.update_lines()
    
    def copy2(self, x, y):
        ele = self.__copy__()
        ele.move(x - self.left, y - self.top)
        return ele
    
    def render(self, drawer):
        # super().render(drawer)
        for line in self.lines:
            line.render(drawer)
            
        if self.visible:
            for ele in self:
                ele.render(drawer)
    
    def __str__(self):
        return super().__str__() + '{' + ','.join(
            [str(i) for i in self.data]) + '}'


@lru_cache
def load_font(font_path, font_size):
    return ImageFont.truetype(font_path, font_size)


def textbbox(pos, txt, font, anchor, stroke_width=0):
    box = font.getbbox(txt, anchor=anchor, stroke_width=stroke_width)
    return box[0] + pos[0], box[1] + pos[1], box[2] + pos[0], box[3] + pos[1]


class Label:
    """
    标签类
    """
    
    def __init__(self, content: str, rect: Rect, key: str):
        self.key = key
        self.content = content
        self.rect = rect
    
    @property
    def points(self):
        return [
            self.rect.topleft,
            self.rect.topright,
            self.rect.bottomright,
            self.rect.bottomleft,
        ]
    
    def __str__(self):
        return ";".join(
            map(
                str,
                [
                    *self.rect.topleft,
                    *self.rect.topright,
                    *self.rect.bottomright,
                    *self.rect.bottomleft,
                    f"{self.key}@{self.content}",
                ],
            )
        )


def draw_text(
        pos,
        txt,
        font_path,
        font_size,
        fill=(0, 0, 0, 255),
        anchor="lt",
        stroke_width=0,
        stroke_fill=None,
        underline=False,
        deleteline=False,
):
    """
    将任何锚点的字符串转化成 lt 锚点，并且去除前后空格
    :param pos: 锚点位置(x,y)
    :param txt: str 文本
    :param font_path: str 字体
    :param font_size: int 字体像素高
    :param fill: 填充颜色
    :param anchor: str 锚点类型
    :return:
    """
    if txt == txt.strip():
        return Text(
            pos,
            txt,
            fill,
            font_path,
            font_size,
            anchor,
            stroke_width,
            stroke_fill,
            underline,
            deleteline,
        )
    
    font = load_font(font_path, font_size)
    box = textbbox(pos, txt, font, anchor, stroke_width)
    
    if txt != txt.rstrip():  # 右边有空格
        txt = txt.rstrip()
        pos = box[0], (box[1] + box[3]) // 2
        box = textbbox(pos, txt, font, "lm", stroke_width)  # 左对齐的方式写字
        anchor = "lm"
    
    if txt != txt.lstrip():  # 左边有空格
        txt = txt.lstrip()
        pos = box[2], (box[1] + box[3]) // 2  # 右中点
        anchor = "rm"
    
    return Text(
        pos,
        txt.strip(),
        fill,
        font_path,
        font_size,
        anchor,
        stroke_width,
        stroke_fill,
        underline,
        deleteline,
    )


class Text(Element):
    def __init__(
            self,
            xy=(0, 0),
            text="",
            fill=None,
            font_path="simfang.ttf",
            font_size=20,
            anchor=None,
            stroke_width=0,
            stroke_fill=None,
            underline=False,
            deleteline=False,
    ):
        self._xy = xy
        self._text = text
        self._fill = fill
        self._font_path = font_path
        self._font_size = font_size
        self._anchor = anchor
        self._stroke_width = stroke_width
        self._stroke_fill = stroke_fill
        self._font = load_font(self._font_path, self._font_size)
        
        box = self.bbox
        super().__init__(box[0], box[1], box[2] - box[0], box[3] - box[1])
        self._underline = underline
        if underline:
            self._line_fills[3] = self._fill
        if deleteline:
            self._deleteline = Line(self.midleft, self.midright, 1, self._fill)
        else:
            self._deleteline = False
    
    def copy(self):
        return Text(
            self._xy,
            self._text,
            self._fill,
            self._font_path,
            self._font_size,
            self._anchor,
            self._stroke_width,
            self._stroke_fill,
            self._underline,
            self._deleteline,
        )
    
    def move(self, dx, dy):
        self.xy = self.xy[0] + dx, self.xy[1] + dy
        self.update_lines()
    
    def cmove(self, dx, dy):
        t = self.copy()
        t.move(dx, dy)
        return t
    
    def update_lines(self, oldbox=None, newbox=None):
        """如果改变位置，文字，字体式时，更新坐标"""
        box = self.bbox
        self._left = box[0]
        self._top = box[1]
        self._right = box[2]
        self._bottom = box[3]
        super().update_lines(oldbox, newbox)
    
    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, val):
        self._text = val
        self.update_lines()
    
    @property
    def xy(self):
        return self._xy
    
    @xy.setter
    def xy(self, val):
        self._xy = val
        self.update_lines()
    
    @property
    def fill(self):
        return self._fill
    
    @fill.setter
    def fill(self, val):
        self._fill = val
        if self._deleteline:
            self._deleteline.fill = self._fill
    
    @property
    def deleteline(self):
        return self._deleteline
    
    @deleteline.setter
    def deleteline(self, val):
        if val:
            self._deleteline = Line(self.midleft, self.midright, 1, self._fill)
        else:
            self._deleteline = None
    
    @property
    def underline(self):
        return self._bottom_line
    
    @underline.setter
    def underline(self, val):
        self._underline = val
        self._line_fills[3] = self._fill
        self.update_lines()
    
    @property
    def anchor(self):
        return self._anchor
    
    @anchor.setter
    def anchor(self, val):
        self._anchor = val
        self.update_lines()
    
    @property
    def font_path(self):
        return self._font_path
    
    @font_path.setter
    def font_path(self, val):  # 改变字体时候自动重新加载字体
        self._font_path = val
        self._font = load_font(self._font_path, self._font_size)
        self.update_lines()
    
    @property
    def font_size(self):
        return self._font_size
    
    @font_size.setter
    def font_size(self, val):  # 改变字号时候自动重新加载字体
        self._font_size = val
        self._font = load_font(self._font_path, self._font_size)
        self.update_lines()
    
    @property
    def stroke_width(self):
        return self._stroke_width
    
    @stroke_width.setter
    def stroke_width(self, val):
        self._stroke_width = val
        self.update_lines()
    
    @property
    def bbox(self):
        box = self._font.getbbox(
            self.text, anchor=self.anchor, stroke_width=self._stroke_width
        )
        return (
            box[0] + self.xy[0],
            box[1] + self.xy[1],
            box[2] + self.xy[0],
            box[3] + self.xy[1],
        )
    
    @property
    def label(self):
        return Label(self.text, self, key="text")
    
    def render(self, drawer: ImageDraw):
        drawer.text(
            self._xy,
            self._text,
            self.fill,
            self._font,
            self._anchor,
            stroke_width=self._stroke_width,
            stroke_fill=self._stroke_fill,
        )
        super().render(drawer)
        # if self._deleteline:
        #     self._deleteline.render(drawer)
        # if self._underline:
        #     self._bottom_line.render(drawer)
    
    def __contains__(self, item):
        return item in self._text
    
    def __str__(self):
        return self._text
    
    def show(self):
        im = Image.new("RGBA", self.bottomright, (255, 255, 255, 255))
        drawer = ImageDraw.Draw(im)
        self.render(drawer)
        im.crop(self.bbox).show(self._text)


class TextBox(Box):
    """文本框"""


def draw_dash_line(drawer, start, end, fill, width, dash=4, gap=2):
    if start[0] == end[0]:
        for y in range(start[1], end[1], dash + gap):
            _s = start[0], y
            _e = start[0], min(y + dash, end[1])
            
            drawer.line((_s, _e), fill, width)
    if start[1] == end[1]:
        for x in range(start[0], end[0], dash + gap):
            _s = x, start[1]
            _e = min(end[0], x + dash), start[1]
            drawer.line((_s, _e), fill, width)
    raise ValueError("The Line is neither vertical nor hor")


class Line:
    def __init__(self, start, end, width=1, fill=(0, 0, 0, 0), mode="s"):
        self.start = start
        self.end = end
        self.width = width
        self.fill = fill
        self.mode = mode
    
    @property
    def is_ver(self):
        return self.start[0] == self.end[0]
    
    @property
    def is_hor(self):
        return self.start[1] == self.end[1]
    
    def copy(self):
        return Line(self.start, self.end, self.width, self.fill)
    
    def move(self, x, y):
        self.start = self.start[0] + x, self.start[1] + y
        self.end = self.end[0] + x, self.end[1] + y
    
    def cmove(self, x, y):
        line = self.copy()
        line.move(x, y)
        return line
    
    def smove(self, dx, dy=0):  # 起点移动
        self.start = self.start[0] + dx, self.start[1] + dy
    
    def emove(self, dx, dy=0):  # 终点移动
        self.end = self.end[0] + dx, self.end[1] + dy
    
    def render(self, drawer: ImageDraw):
        if self.mode == "s":
            drawer.line((self.start, self.end), fill=self.fill,
                        width=self.width)
        elif self.mode == "d":
            draw_dash_line(drawer, self.start, self.end, self.fill, self.width)
        elif self.mode[0] == "s" and "d" in self.mode:
            solid, gap = self.mode[1:].split("d")
            draw_dash_line(
                drawer,
                self.start,
                self.end,
                self.fill,
                self.width,
                int(solid),
                int(gap),
            )
    
    def __str__(self):
        return f"Line({self.start[0]},{self.start[1]},{self.end[0]},{self.end[1]})"


class Cell(Box):
    """
    单元格内部的对齐方式需不需要
    todo 超出单元格怎么办
    todo 排列
    """
    
    def __init__(self, initlist=None, align=None, padding_width=0, *args,
                 **kwargs):
        super().__init__(initlist, *args, **kwargs)
        self._align = align
        self._paddings = []
        self._set_paddings(padding_width)
        if align:
            self._do_align()
    
    def _do_align(self):
        if self.align == "mm":
            for text in self:
                text.xy = self.center
                text.anchor = "mm"
        
        elif self.align == "lm":
            for text in self:
                text.xy = self.left + self._paddings[0], self.centery
                text.anchor = "lm"
        
        elif self.align == "rm":
            for text in self:
                text.xy = self.right - self._paddings[2], self.centery
                text.anchor = "rm"
        
        elif self.align == "lt":
            for text in self:
                text.xy = self.left + self._paddings[0], self.top + \
                          self._paddings[1]
                text.anchor = "lt"
        
        elif self.align == "rt":
            for text in self:
                text.xy = self.right - self._paddings[2], self.top + \
                          self._paddings[1]
                text.anchor = "rt"
        
        elif self.align == "mt":
            for text in self:
                text.xy = self.centerx, self.top + self._paddings[1]
                text.anchor = "mt"
        
        elif self.align == "lb":
            for text in self:
                text.xy = (
                    self.left + self._paddings[0],
                    self.bottom - self._paddings[3],
                )
                text.anchor = "lb"
        
        elif self.align == "rb":
            for text in self:
                text.xy = (
                    self.right - self._paddings[2],
                    self.bottom - self._paddings[3],
                )
                text.anchor = "rb"
        
        elif self.align == "mb":
            for text in self:
                text.xy = self.centerx, self.bottom - self._paddings[3]
                text.anchor = "mb"
    
    @property
    def align(self):
        return self._align
    
    @align.setter
    def align(self, val):
        assert len(val) == 2
        self._align = val
        self._do_align()
    
    @property
    def paddings(self):
        return self._paddings
    
    @paddings.setter
    def paddings(self, val):
        self._set_paddings(val)
        self._do_align()
    
    def _set_paddings(self, val):
        if isinstance(val, int):
            self._paddings = [val] * 4
        elif isinstance(val, (tuple, list)):
            if len(val) == 2:
                self._paddings = [*val, *val]
            elif len(val) == 4:
                self._paddings = list(val)
            else:
                raise ValueError("padding_with is int or list")
        else:
            raise ValueError("padding_with is int or list")
    
    def update_data(self):
        self._do_align()
    # def update_lines(self, oldbox=None, newbox=None):
    #     self._do_align()
    #     super().update_lines()
    
    @property
    def label(self):
        return Label("", self, key="cell")


class Row(Box):
    """保持内部的cell有序，可以用heap"""
    
    def __init__(self, cells: List[Cell] = None, *args, **kwargs):
        super(Row, self).__init__(cells, *args, **kwargs)
        self.update_row()
    
    # def update(self,oldbox=None,newbox=None):
    #     # self.update_row()
    #     super().update()
        
    def update_row(self):
        """更新行时会自动更新线"""
        self.data.sort(key=lambda x: x.left)
        self._left = self.data[0].left
        self._top = min(c.top for c in self.data)
        self._width = self.data[-1].right - self._left  # self.width 会更新
        self._height = max(c.bottom for c in self.data) - self.top
    
    # todo 更新线时更新行内单元格
    def update_data(self):
        """更新单元格形状"""
        self.data.sort(key=lambda x: x.left)
        
        self.data[0]._width = self.data[0].right - self.left
        self.data[0]._left = self.left
        
        self.data[-1]._width = self.right - self.data[-1].left
        self.data[-1]._right = self.right
        
        for cell in self.data:
            cell._top = self.top
            cell._height = self.height
            cell._do_align()
    
    # def update_lines(self, oldbox=None, newbox=None):
    #     super().update_lines()
        # self.update_cells()
    
    def merge(self, start, end):
        """合并单元格 左闭右开"""
        cell = self.data[start]
        for i in range(start + 1, end):
            cell += self.data[i]
            del self.data[i]
    
    @property
    def label(self):
        return Label("", self, key="row")


class Col(Box):
    """保持内部的cell有序，可以用heap"""
    
    def __init__(self, cells: List[Cell] = None, *args, **kwargs):
        super(Col, self).__init__(cells, *args, **kwargs)
        self.update_col()
    
    def update_col(self):
        """更新行时会自动更新线"""
        self.data.sort(key=lambda x: x.top)
        self._left = min(c.left for c in self.data)
        self._top = self.data[0].top
        self._width = max(c.right for c in self.data) - self._left  # self.width
        # 会更新
        self.height = max(c.bottom for c in self.data) - self.top
    
    # todo 更新线时更新行内单元格
    def update_data(self):
        """更新单元格形状"""
        self.data[0]._height = self.data[0].bottom - self.top
        self.data[0]._top = self.top
        
        self.data[-1]._height = self.bottom - self.data[-1].top
        self.data[-1]._bottom = self.bottom
        
        for cell in self.data:
            cell._left = self.left
            cell._width = self.width
            # cell._do_align()
    
    def merge(self, start, end):
        """合并单元格 左闭右开"""
        cell = self.data[start]
        for i in range(start + 1, end):
            cell += self.data[i]
            del self.data[i]
    
    # def update_lines(self, oldbox=None, newbox=None):
        # super().update_lines()
        # self.update_cells()


class Table(Col):
    """表格不是基本元素，是容器元素"""
    
    def __init__(self, initlist: List[Row] = None,*args,**kwargs):
        if initlist:
            if isinstance(initlist[0],Cell):
                initlist = self.from_cells(initlist)
        
        super().__init__(initlist,*args,**kwargs)
    
    @staticmethod
    def from_cells(cells):
        d = defaultdict(list)
        for cell in cells:
            d[cell.top].append(cell)
        rows = []
        for k in sorted(list(d.keys())):
            rows.append(Row(d[k]))
        return rows
    
    def update_data(self):
        """重新计算行的位置和高度"""
        self.data.sort(key=lambda r: r.top)
        self._left = min(r.left for r in self.data)
        self._top = self.data[0].top
        self._width = max(r.right for r in self.data) - self.left
        self._height = self.data[-1].bottom
        for row in self.data:
            row._left = self.left
            row._width = self.width
            row.update_data()
    
    # def append_row(self, row: Row):
    #     self._rows.append(row)
    #     self.update()
    #
    # def copy_row(self, rno):
    #     row = self._rows[rno]
    #     copyed = row.copy()
    #     copyed.top = row.bottom
    #     self.append_row(row)
    
    # def insert_after(self, row, rno):
    #     t = self._rows[rno]
    #     row.top = t.bottom
    #     for r in self._rows[rno + 1:]:
    #         r.top += row.height
    #     self.append_row(row)
    
    # def insert_before(self, row, rno):
    #     if rno == 0:
    #         row.top = self._rows[0].top
    #         for r in self._rows:
    #             r.top += row.height
    #     else:
    #         self.insert_after(row, rno - 1)
    
    # def add_row(self):
    #     self.insert_after(self._rows[-1].copy(), len(self._rows) - 1)
    
    # def merge_rows(self, start, end):
    #     pass
    
    # @property
    # def outline(self):
    #     return self._outline
    #
    # @outline.setter
    # def outline(self, val):
    #     self._outline = val
    #     self.update_lines()
    
    # @property
    # def line_width(self):
    #     return self._line_width
    #
    # @line_width.setter
    # def line_width(self, val):
    #     self._line_width = val
    #     self.update_lines()
    
    # def __iter__(self):
    #     for row in self._rows:
    #         for cell in row:
    #             yield cell
    #
    # def __getitem__(self, item):
    #     """可以取单元格或者某行
    #     table[0] 是第0行
    #     table[0][0] 是第0行第0列的cell
    #     """
    #     return self._rows[item]
    
    # def merge(self, row_start, col_start, row_end, col_end):
    #     """合并单元格"""
    #     self._rows[row_start][row_start].merge(self._rows[row_end][col_end])
    #     self._rows[row_end][col_end].visible = False  # 不可以直接删除，标记为删除
    
    @property
    def label(self):
        labels = []
        for row in self.data:
            for cell in row:
                if cell.visible:
                    labels.append(cell.label)
                    for text in cell.texts:
                        labels.append(text.label)
        return labels
    
    # def render(self, drawer):
    #     for row in self.data:
    #         for cell in row:
    #             if cell.visible:
    #                 cell.render(drawer)
    #     for line in self.lines:
    #         line.render(drawer)


class ImageInfo(Rect):
    def __init__(self, image: Image, box=None, mask=None):
        if not box:
            box = (0, 0)
        if len(box) == 2:
            super().__init__(box[0], box[1])
        elif len(box) == 4:
            super().__init__(box[0], box[1], box[2] - box[0], box[3] - box[1])
        
        self.image = image
        if mask:
            self.mask = mask
        else:
            if self.image.mode in ("L", "RGBA"):
                self.mask = self.image
            else:
                self.mask = None
    
    @property
    def label(self):
        return Label("", self, key="image")


class Layer(list):
    """图层容器"""
    
    def __init__(self, name="texts", index=0, size=None):
        super().__init__()
        self.index = index
        self.name = name
        self.size = size
    
    def render(self):
        im = Image.new("RGBA", self.size, (0, 0, 0, 0))
        drawer = ImageDraw.Draw(im)
        for obj in self:
            obj.render(drawer)
        return im


class ImageData:
    def __init__(
            self,
            background: Image,
            texts: List[Text] = None,
            images: List[ImageInfo] = None,
            lines: List[Line] = None,
            tables: List[Table] = None,
            **kwargs,
    ):
        self.background = background
        self.texts = texts or []
        self.lines = lines or []
        self.images = images or []
        self.tables = tables or []
        self.size = background.size
    
    @classmethod
    def new(cls, size, color=(0, 0, 0, 0)):
        background = Image.new("RGBA", size, color)
        return cls(background)
    
    @property
    def text_layer(self):
        layer = Layer("text", 1, self.size)
        for table in self.tables:
            for cell in table.cells:
                for text in cell.texts:
                    layer.append(text)
        layer.extend(self.texts)
        return layer
    
    @property
    def line_layer(self):
        layer = Layer("line", 2, self.size)
        for table in self.tables:
            for cell in table.cells:
                for line in cell.lines:
                    layer.append(line)
        layer.extend(self.lines)
        return layer
    
    @property
    def text_image(self):
        return self.text_layer.render()
    
    @property
    def line_image(self):
        return self.line_layer.render()
    
    @property
    def doc_image(self):
        text_image = self.text_image
        line_image = self.line_image
        text_image.paste(line_image, mask=line_image)
        return text_image
    
    @property
    def image(self):
        bg = self.background.copy()
        bg.paste(self.doc_image, mask=self.doc_image)
        for im in self.images:
            bg.paste(im.image, im.topleft, mask=im.mask)
        return bg
    
    @property
    def mask(self):
        return self.image.getchannel("A")
    
    def show(self):
        self.image.show()
    
    def save(self, filename):
        self.image.convert("RGB").save(filename)
        log_file = filename.split(".")[0] + ".txt"
        with open(log_file, "w", encoding="utf-8") as f:
            for label in self.label:
                f.write(f"{filename};{str(label)}\n")
    
    @property
    def label(self):
        labels = []
        for text in self.texts:
            labels.append(text.label)
        for table in self.tables:
            labels.extend(table.label)
        return labels
    
    def text(self, pos, txt, font_path, font_size, fill=(0, 0, 0, 255),
             anchor="lt"):
        self.texts.append(
            draw_text(pos, txt, font_path, font_size, fill, anchor))
    
    def line(self, start, end, width=1, fill="black", mode="s"):
        self.lines.append(Line(start, end, width, fill, mode))
    
    def paste(self, im, box=None, mask=None):
        self.images.append(ImageInfo(im, box, mask))
    
    def asdict(self):
        d = {}
        d["image"] = self.image
        d["label"] = [f"{label.key}@{label.content}" for label in self.label]
        points = []
        for label in self.label:
            points.extend(label.points)
        d["point"] = points
        return d


class TableGenerator:
    def build_table(self):
        """构建文本表格"""
    
    def load_template(self):
        """表格转imagedata"""
    
    def preprocess(self, template):
        """表格预处理
        1.添加、修改文字颜色，字体
        2.绘制可见线
        """
    
    def render(self, template):
        """
        渲染表格，生成image_dict
        """
    
    def postprocess(self, image_data):
        """
        处理图像相关的
        """


if __name__ == "__main__":
    # c = Cell()
    # b = Text((0, 0), "儿")
    # print(c)
    # print(b)
    # c.append(b)
    #
    # d = Cell()
    # d.append(b.copy())
    # print(c)
    #
    # e = c + d
    # print(e)
    im = Text(
        (100, 100),
        "中国",
        (255, 0, 0, 255),
        "simfang.ttf",
        50,
        underline=True,
        deleteline=True,
    )
    cell = Cell(
        None,
        "mm",
        0,
        0,
        0,
        200,
        200,
        outline=(0, 0, 0, 255),
        line_width=2,
    )
    
    cell.append(im)
    # cell.show()
    # cell.width *= 2
    # cell.height = cell.height // 2
    # cell.do_align()
    # cell.paddings = 0
    
    # cell.copy()
    # cell.show()
    cell2 = Cell(
        None,
        "mm",
        0,
        200,
        0,
        200,
        200,
        outline=(0, 0, 0, 255),
        line_width=2,
    )
    
    # cell.show()
    # cell2.show()
    # c = cell+cell2
    # print(c)
    # c.show()
    # cell+=cell2
    # cell.show()
    row = Row([cell, cell2, cell.copy2(400, 0)])
    row1 = row.copy2(0,200)
    # row1.show()
    t = Table([row,row1])
    # print(row)
    # row.height = 50
    # row.merge(0, 2)
    # row.show()
    print(t)
    # t.show()
    row1.height //=2
    t[1][0][0].fill = (0,255,0,255)
    # t[1][0].align = 'lb'
    t.show()

