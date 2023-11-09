"""
管理布局模块
"""
import textwrap
from abc import ABCMeta, abstractmethod

import cv2
import numpy as np
import prettytable
from PIL import Image, ImageFont

from awesometable.awesometable import AwesomeTable
from awesometable.fontwrap import (put_text_in_box,
                                   put_text_in_box_without_break_word)
from awesometable.table2image import Text, table2image
from postprocessor.convert import as_image, p2c


def _modify_text(text, pos):
    x_0, y_0 = pos
    x_1, y_1, x_2, y_2 = text.box
    x_3, y_3 = text.xy
    text.box = x_1 + x_0, y_1 + y_0, x_2 + x_0, y_2 + y_0
    text.xy = x_3 + x_0, y_3 + y_0


def _modify_line(line, pos):
    x_0, y_0 = pos
    x_1, y_1 = line.start
    x_2, y_2 = line.end
    line.start = x_1 + x_0, y_1 + y_0
    line.end = x_2 + x_0, y_2 + y_0


class LayoutTable(AwesomeTable):
    """布局文字布局管理"""
    
    def __init__(self, field_names=None, **kwargs):
        super().__init__(field_names, kwargs=kwargs)
        self.vrules = prettytable.FRAME
        self.hrules = prettytable.NONE
        self._padding_width = 0
        self._left_padding_width = 0
        self._right_padding_width = 0
        self.hide_outlines()
    
    def hide_outlines(self):
        """隐藏制表符"""
        self._horizontal_char = ""
        self._vertical_char = ""
        self._junction_char = ""
        self._top_junction_char = ""
        self._bottom_junction_char = ""
        self._right_junction_char = ""
        self._left_junction_char = ""
        self._top_right_junction_char = ""
        self._top_left_junction_char = ""
        self._bottom_right_junction_char = ""
        self._bottom_left_junction_char = ""


class AbstractTable(object, metaclass=ABCMeta):
    """抽象表格类"""
    
    def __init__(self):
        self.layouts = []
    
    def __str__(self):
        return str(self.get_string())
    
    @abstractmethod
    def get_string(self):
        """字符表示"""
        return NotImplemented
    
    @property
    def height(self):
        """图像高度"""
        return self.get_image()["image"].shape[0]
    
    # @abstractmethod
    # def get_image(self):
    #     """图片表示"""
    #     return NotImplemented
    
    def append(self, obj):
        """追加布局"""
        if hasattr(obj, "get_image"):
            self.layouts.append(obj)
        else:
            raise ValueError("Not Layout or Table")


class HorLayout(AbstractTable):
    """水平方向布局的抽象
    任何实现了 get_image 方法和 table_width 属性的类表格，
    均可作为布局管理的 layouts列表的子元素，包括布局自身
    """
    
    def __init__(self, layouts=None, widths=None, gaps=None):
        """
        :param layouts: list 布局元素列表
        :param widths: int|list[int]|None 各个元素的宽度
        :param gaps: int|list[int]|None 各个元素之间的间隔
        """
        super().__init__()
        self.layouts = layouts or []
        
        if isinstance(widths, int):
            self._widths = [widths] * len(self.layouts)
        elif isinstance(widths, list):
            self._widths = widths
        else:
            self._widths = [x.table_width for x in self.layouts]
        
        if isinstance(gaps, int):
            self._gaps = [gaps] * (len(self.layouts) - 1)
        elif isinstance(gaps, list):
            self._gaps = gaps
        else:
            self._gaps = [0] * (len(self.layouts) - 1)
        # _char_width 是字符属性 _table 是图像属性
        
        # self._char_width = sum(x + 1 for x in self._widths) - 1
        
        self._table_width = sum(self._widths) + sum(self._gaps)
        self.table = LayoutTable()
    
    @property
    def table_width(self):
        """图片宽度"""
        return self._table_width
    
    @table_width.setter
    def table_width(self, val):
        self._table_width = val
    
    @property
    def widths(self):
        """元素宽度列表"""
        return self._widths
    
    @widths.setter
    def widths(self, val):
        self._widths = val
    
    def get_string(self):
        row = []
        for lot, width in zip(self.layouts, self._widths):
            lot.table_width = width
            row.append(str(lot))
        self.table.clear_rows()
        self.table.add_row(row)
        return self.table.get_string()
    
    def get_image(self):
        cols = []
        out = {}
        for lot, wid in zip(self.layouts, self._widths):
            lot.table_width = wid
            imgc = lot.get_image()
            cols.append(imgc)
        # 计算背景尺寸
        hei = max(col["image"].shape[0] for col in cols)
        wid = sum(col["image"].shape[1] for col in cols) + sum(self._gaps)
        img = np.ones((hei, wid, 3), np.uint8) * 255
        ptx = 0
        pty = 0
        gaps = self._gaps + [0]
        for data, gap in zip(cols, gaps):
            hei, wid = data["image"].shape[:2]
            img[pty: pty + hei, ptx: ptx + wid] = data["image"]
            data["points"] = (np.array(data["points"]) + (ptx, pty)).tolist()
            for text in data["text"]:
                _modify_text(text, (ptx, pty))
            for line in data["line"]:
                _modify_line(line, (ptx, pty))
            
            if not out:
                out = data
            else:
                out["image"] = img
                out["label"].extend(data["label"])
                out["points"].extend(data["points"])
                out["text"].extend(data["text"])
                out["line"].extend(data["line"])
            ptx += wid + gap
        return out


class VerLayout(AbstractTable):
    """输入二维列表，输出竖直布局"""
    
    def __init__(self, layouts=None, widths=None, gaps=None):
        """
        :param layouts: list 布局元素列表
        :param widths: int|list[int]|None 各个元素的宽度
        :param gaps: int|list[int]|None 各个元素之间的间隔
        """
        super().__init__()
        self.layouts = layouts or []
        if isinstance(widths, int):
            self._widths = [widths] * len(self.layouts)
            self._table_width = widths
        elif isinstance(widths, list):
            self._widths = widths
            self._table_width = max(widths)
        else:
            print(self.layouts)
            self._table_width = max([x.table_width for x in self.layouts])
            self._widths = [self._table_width] * len(self.layouts)
        
        if isinstance(gaps, int):
            self._gaps = [gaps] * (len(self.layouts) - 1)
        elif isinstance(gaps, list):
            self._gaps = gaps
        else:
            self._gaps = [0] * (len(self.layouts) - 1)
        
        self.table = LayoutTable()
    
    @property
    def table_width(self):
        """图片宽度"""
        return self._table_width
    
    @table_width.setter
    def table_width(self, val):
        self._table_width = val
        self._widths = [self._table_width] * len(self.layouts)
    
    def get_string(self):
        row = []
        for lot, wid in zip(self.layouts, self._widths):
            lot.table_width = wid
            row.append([str(lot)])
        self.table.clear_rows()
        self.table.add_rows(row)
        return self.table.get_string()
    
    def get_image(self):
        rows = []
        out = {}
        for lot, wid in zip(self.layouts, self._widths):
            lot.table_width = wid
            imgc = lot.get_image()
            rows.append(imgc)
        
        hei = sum(row["image"].shape[0] for row in rows) + sum(self._gaps)
        wid = max(row["image"].shape[1] for row in rows)
        img = np.ones((hei, wid, 3), np.uint8) * 255
        ptx = 0
        pty = 0
        gaps = self._gaps + [0]
        for data, gap in zip(rows, gaps):
            hei, wid = data["image"].shape[:2]
            img[pty: pty + hei, ptx: ptx + wid] = data["image"]
            data["points"] = (np.array(data["points"]) + (ptx, pty)).tolist()
            for text in data["text"]:
                _modify_text(text, (ptx, pty))
            for line in data["line"]:
                _modify_line(line, (ptx, pty))
            if not out:
                out = data
            else:
                out["image"] = img
                out["label"].extend(data["label"])
                out["points"].extend(data["points"])
                out["text"].extend(data["text"])
                out["line"].extend(data["line"])
            pty += hei + gap
        return out


class FlexTable(AwesomeTable):
    """在 awesometable 基础上增加 tablewith 像素尺度
    英文字体大多都是非等宽字体，如果按行左对齐则右边参差补齐
    """
    
    def __init__(self, width=None, font_size=40, **kwargs):
        """
        :param width: int 图片宽度
        :param font_size: int 字体大小
        :param kwargs:
        """
        super().__init__(**kwargs)
        self.font_size = font_size
        self.options = kwargs
        if width is not None:
            self._table_width = width  # 像素尺寸
            self.min_table_width = width * 2 // self.font_size - 1
            self.max_table_width = width * 2 // self.font_size - 1
    
    @property
    def table_width(self):
        """图片宽度"""
        return self._table_width
    
    @table_width.setter
    def table_width(self, val):
        self._validate_option("table_width", val)
        self.min_table_width = val * 2 // self.font_size - 1
        self._table_width = val
        self.max_table_width = val * 2 // self.font_size - 1
    
    @property
    def height(self):
        """图片高度"""
        return (len(str(self).splitlines())) * (self.font_size - 2)
    
    def get_image(self):
        """图像表示"""
        return table2image(
            str(self),
            font_size=self.font_size,
            vrules=None,
            hrules=None,
            style=self.style,
            **self.options
        )


class TextBlock(AbstractTable):
    """
    文本块元素,其高度是被动决定的
    """
    
    def __init__(
            self,
            text,
            width=None,
            indent=0,
            font_path="arial.ttf",
            font_size=20,
            padding=0,
            fill="black",
            **kwargs
    ):
        """
        :param text: str 文本
        :param width: int 图片宽
        :param indent: int 缩进量
        :param font_path: str 字体路径
        :param font_size: int 字体大小
        :param padding: int 四周填充宽度
        :param fill: tuple|str 字体颜色
        :param kwargs:
        """
        super().__init__()
        self._text = text
        self.indent = indent
        if width:
            self._table_width = width
            self._char_width = 2 * width // font_size
        else:
            self._table_width = None
            self._char_width = None
        self.align = kwargs.get("align", "l")
        self.font_size = font_size
        self.font_path = font_path
        self.padding = padding
        self.fill = fill
    
    @property
    def text(self):
        """文本"""
        return " " * self.indent + self._text
    
    @property
    def wrap_text(self):
        """打包文本"""
        return textwrap.wrap(self.text, self._char_width)
    
    @property
    def table_width(self):
        """图像宽度"""
        return self.get_image()['image'].shape[1]
    
    @table_width.setter
    def table_width(self, val):
        self._table_width = val
    
    @staticmethod
    def double_end_align(text: str, width: int):
        """
        两端对齐文本
        :param text: str 多行文本
        :param width: int 文本宽度
        :return: str
        """
        lines = text.splitlines()
        newlines = []
        for line in lines[:-1]:
            newline = ""
            words = line.split()
            spaces = width - sum(len(wid) for wid in words)
            if len(words) > 1:
                gaps = len(words) - 1
                breaks = [spaces // gaps] * gaps
                for i in range(spaces % gaps):
                    breaks[i] += 1
                breaks.append(0)
                for wid, brk in zip(words, breaks):
                    newline += wid
                    newline += " " * brk
            else:
                newline += words
            newlines.append(newline)
        newlines.append(lines[-1])
        return "\n".join(newlines)
    
    def get_string(self):
        if self.align == "d":
            return self.double_end_align("\n".join(self.wrap_text),
                                         self._char_width)
        return put_text_in_box(self.text, self._table_width, break_word=False)[
            0]
    
    def get_image(self):
        txt, img, boxes = put_text_in_box_without_break_word(
            self.text,
            self._table_width,
            self.indent,
            self.fill,
            font_size=self.font_size,
            font_path=self.font_path,
        )
        texts = [
            Text(
                (b[0], b[1]),
                text,
                ImageFont.truetype(self.font_path, self.font_size),
                "lt",
                self.fill,
                b,
            )
            for b, text in zip(boxes, txt.splitlines())
        ]
        
        if self.padding != 0:
            back = Image.new(
                "RGB",
                (img.width + self.padding * 2, img.height + self.padding * 2),
                "white",
            )
            back.paste(img, (self.padding, self.padding))
            for text in texts:
                _modify_text(text, (self.padding, self.padding))
            img = back
        
        points = []
        for box in boxes:
            points.append([box[0] + self.padding, box[1] + self.padding])
            points.append([box[2] + self.padding, box[1] + self.padding])
            points.append([box[2] + self.padding, box[3] + self.padding])
            points.append([box[0] + self.padding, box[3] + self.padding])
        
        return {
            "image" : cv2.cvtColor(np.asarray(img, np.uint8),
                                   cv2.COLOR_RGB2BGR),
            "points": points,
            "label" : ["text@" + l for l in txt.splitlines()],
            "text"  : texts,
            "line"  : [],
        }


class Cell(TextBlock):
    """单元格表示"""
    
    def __init__(self, text, **kwargs):
        super().__init__(text, **kwargs)
        self.outline = kwargs.get('outline', (0, 0, 0))
        self.line_width = kwargs.get('line_width', 1)
        self.bg_color = kwargs.get('bg_color', (255, 255, 255))
    
    def get_image(self):
        data = super().get_image()
        img = data['image']
        height, width = img.shape[:2]
        data['image'] = cv2.rectangle(img, (0, 0), (
            width - self.line_width, height - self.line_width), self.outline,
                                      self.line_width)
        return data


class TableBlock(AwesomeTable):
    """
    以TextBlock为元素的表格
    """
    
    def __init__(self, rows=None, field_names=None, **kwargs):
        super().__init__(rows=rows, field_names=field_names, **kwargs)
        self.font_path = kwargs.get('font_path', 'arial.ttf')
    
    def parse_layout(self):
        table_block = []
        for col in zip(*self._rows):  # 行列转置
            col_block = []
            for cell in col:
                cell_block = Cell(cell, padding=5, font_path=self.font_path)
                col_block.append(cell_block)
            table_block.append(VerLayout(col_block))
        # print(table_block)
        return HorLayout(table_block)
    
    def get_image(self):
        return self.parse_layout().get_image()
    
    def table_width(self):
        return self.parse_layout().table_width


class ImageBlock:
    def __init__(self, img, width=None, height=None):
        self.image = as_image(img)
        self._width = width or self.image.width
        self._height = height or self.image.height
    
    @property
    def table_width(self):
        return self._width
    
    @table_width.setter
    def table_width(self, val):
        self._width = val
    
    @property
    def height(self):
        return self._height
    
    @height.setter
    def height(self, val):
        self._height = val
    
    def get_image(self):
        return {'image' : p2c(self.image.resize((self._width, self._height))),
                "points": [[0, 0], [self._width, 0], [self._width, self.height],
                           [0, self._height]],
                "label" : ["image@"],
                "text"  : [],
                "line"  : [],
                }
    
    def __str__(self):
        return f"<ImageBlock>{id(self)}-{self._width}x{self._height}"

