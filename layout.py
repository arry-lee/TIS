# __author__ = "arry lee"
# 2022-2-21 17:37:31
# LayoutTable 是用于管理布局的表格

import textwrap
from abc import ABCMeta, abstractmethod

import cv2
import numpy as np
import prettytable
from PIL import Image

from awesometable import AwesomeTable
from fontwrap import put_text_in_box, put_text_in_box_without_break_word
from table2image import table2image


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
    def __init__(self):
        self.layouts = []

    def __str__(self):
        return self.get_string()

    @abstractmethod
    def get_string(self):
        return NotImplemented

    @property
    def height(self):
        return self.get_image()['image'].shape[0]

    @abstractmethod
    def get_image(self):
        return NotImplemented

    def append(self, obj):
        if hasattr(obj, "get_image"):
            self.layouts.append(obj)
        else:
            raise ValueError("Not Layout or Table")

#todo 移除布局类的offset，布局不应该有offset，只有gap
class HorLayout(AbstractTable):
    """水平方向布局的抽象
    任何实现了 get_image 方法和 table_width 属性的类表格，
    均可作为布局管理的 layouts列表的子元素，包括布局自身
    """

    def __init__(self, layouts=None, widths=None,gaps=None):
        super().__init__()
        self.layouts = layouts or []

        if isinstance(widths, int):
            self._widths = [widths] * len(self.layouts)
        elif isinstance(widths, list):
            self._widths = widths
        else:
            self._widths = [x.table_width for x in self.layouts]

        if isinstance(gaps, int):
            self._gaps = [gaps] * (len(self.layouts)-1)
        elif isinstance(gaps, list):
            self._gaps = gaps
        else:
            self._gaps = [0]*(len(self.layouts)-1)
        # _char_width 是字符属性 _table 是图像属性
        self._char_width = sum(x + 1 for x in self._widths) - 1
        self._table_width = sum(self._widths)+sum(self._gaps)
        self.table = LayoutTable()

    @property
    def table_width(self):
        return self._table_width

    @table_width.setter
    def table_width(self, val):
        self._table_width = val

    @property
    def widths(self):
        return self._widths

    @widths.setter
    def widths(self, val):
        self._widths = val

    def get_string(self):
        row = []
        for lot, w in zip(self.layouts, self._widths):
            lot.table_width = w
            row.append(str(lot))
        self.table.clear_rows()
        self.table.add_row(row)
        return self.table.get_string()

    def get_image(self):
        col = []
        out = {}
        for lot, w in zip(self.layouts, self._widths):
            lot.table_width = w
            imgc = lot.get_image()
            col.append(imgc)
        # 计算背景尺寸
        h = max(x["image"].shape[0] for x in col)
        w = sum(x["image"].shape[1] for x in col)+sum(self._gaps)
        img = np.ones((h, w, 3), np.uint8) * 255
        x = 0
        y = 0
        gaps = self._gaps+[0]
        for data,gap in zip(col,gaps):
            h, w = data["image"].shape[:2]
            img[y: y + h, x: x + w] = data["image"]
            data["points"] = (np.array(data["points"]) + (x, y)).tolist()
            if not out:
                out = data
            else:
                out["image"] = img
                out["label"].extend(data["label"])
                out["points"].extend(data["points"])
            x += w+gap
        return out


class VerLayout(AbstractTable):
    """输入二维列表，输出布局"""

    def __init__(self, layouts=None, widths=None,gaps=None):
        super().__init__()
        self.layouts = layouts or []
        if isinstance(widths, int):
            self._widths = [widths] * len(self.layouts)
            self._table_width = widths
        elif isinstance(widths, list):
            self._widths = widths
            self._table_width = max(widths)
        else:
            self._table_width = max([x.table_width for x in self.layouts])
            self._widths = [self._table_width] * len(self.layouts)

        if isinstance(gaps, int):
            self._gaps = [gaps] * (len(self.layouts)-1)
        elif isinstance(gaps, list):
            self._gaps = gaps
        else:
            self._gaps = [0]*(len(self.layouts)-1)

        self.table = LayoutTable()

    @property
    def table_width(self):
        return self._table_width

    @table_width.setter
    def table_width(self, val):
        self._table_width = val
        self._widths = [self._table_width] * len(self.layouts)

    def get_string(self):
        row = []
        for lot, w in zip(self.layouts, self._widths):
            lot.table_width = w
            row.append([str(lot)])
        self.table.clear_rows()
        self.table.add_rows(row)
        return self.table.get_string()

    def get_image(self):
        row = []
        out = {}
        for lot, w in zip(self.layouts, self._widths):
            lot.table_width = w
            imgc = lot.get_image()
            row.append(imgc)

        h = sum(x["image"].shape[0] for x in row)+sum(self._gaps)
        w = max(x["image"].shape[1] for x in row)
        img = np.ones((h, w, 3), np.uint8) * 255
        x = 0
        y = 0
        gaps = self._gaps+[0]
        for data,gap in zip(row,gaps):
            h, w = data["image"].shape[:2]
            img[y: y + h, x: x + w] = data["image"]
            data["points"] = (np.array(data["points"]) + (x, y)).tolist()
            if not out:
                out = data
            else:
                out["image"] = img
                out["label"].extend(data["label"])
                out["points"].extend(data["points"])
            y += h + gap
        return out


class FlexTable(AwesomeTable):
    """ 在 awesometable 基础上增加 tablewith 像素尺度
    英文字体大多都是非等宽字体，如果按行左对齐则右边参差补齐
    """
    def __init__(self, width=None, font_size=40, **kwargs):
        super().__init__(**kwargs)
        self.font_size = font_size
        self.options = kwargs
        if width is not None:
            self._table_width = width #像素尺寸
            self.min_table_width = width * 2 // self.font_size - 1
            self.max_table_width = width * 2 // self.font_size - 1

    @property
    def table_width(self): #按几何尺寸
        return self._table_width

    @table_width.setter
    def table_width(self,val):
        self._validate_option("table_width", val)
        self.min_table_width = val*2//self.font_size-1
        self._table_width = val
        self.max_table_width = val*2//self.font_size-1

    @property
    def height(self):
        return (len(str(self).splitlines())) * (self.font_size-2)
        # return self.get_image()['image'].shape[0] # todo 优化提速

    def get_image(self):
        return table2image(str(self),font_size=self.font_size,vrules=None,hrules=None,style=self.style,**self.options)


class TextBlock(AbstractTable):
    def __init__(self, text, width=70 * 20, indent=0, font_path="arial.ttf",
                 font_size=20, padding=0, fill='black',**kwargs):
        super().__init__()
        self._text = text
        self.indent = indent
        self._table_width = width
        self._char_width = 2*width//font_size
        self.align = kwargs.get("align", "l")
        self.font_size = font_size
        self.font_path = font_path
        self.padding = padding
        self.fill=fill
    @property
    def text(self):
        return " " * self.indent + self._text

    @property
    def wrap_text(self):
        return textwrap.wrap(self.text, self._char_width)

    @property
    def table_width(self):
        return self._table_width

    @table_width.setter
    def table_width(self, val):
        self._table_width = val

    @staticmethod
    def double_end_align(text: str, width: int):
        lines = text.splitlines()
        newlines = []
        for line in lines[:-1]:
            newline = ""
            words = line.split()
            spaces = width - sum(len(w) for w in words)
            if len(words) > 1:
                gaps = len(words) - 1
                n = spaces // gaps
                m = spaces % gaps
                breaks = [n] * gaps
                for i in range(m):
                    breaks[i] += 1
                breaks.append(0)
                for w, b in zip(words, breaks):
                    newline += w
                    newline += " " * b
            else:
                newline += words
            newlines.append(newline)
        newlines.append(lines[-1])
        return "\n".join(newlines)

    def get_string(self):
        if self.align == "d":
            s = "\n".join(self.wrap_text)
            return self.double_end_align(s, self._char_width)
        else:
            return put_text_in_box(self.text, self._table_width, break_word=False)[0]

    def get_image(self):
        s, img,boxes = put_text_in_box_without_break_word(
            self.text,
            self._table_width,
            self.indent,
            self.fill,
            font_size=self.font_size,
            font_path=self.font_path,
        )

        bg = Image.new("RGB", (img.width + self.padding * 2, img.height + self.padding * 2),
                       "white")
        bg.paste(img, (self.padding, self.padding))
        points = []
        for box in boxes:
            points.append([box[0]+self.padding, box[1]+self.padding])
            points.append([box[2]+self.padding, box[1]+self.padding])
            points.append([box[2]+self.padding, box[3]+self.padding])
            points.append([box[0]+self.padding, box[3]+self.padding])

        return {
            "image" :cv2.cvtColor(np.asarray(bg, np.uint8), cv2.COLOR_RGB2BGR),
            "points":points,
            "label" :["text@"+l for l in s.splitlines()],
        }


class TextTable(FlexTable):
    """不再关注表格的字符串表示，用TextBlock表示单元格"""

    def __init__(self, width=None, ratio=None, font_size=40, **kwargs):
        super().__init__(width, font_size, **kwargs)
        self.ratio = ratio

    def _compute_col_widths(self):
        w = self._table_width
        l = self.__getattr__("colcount")
        if self.ratio is None:
            self.col_widths = [w//l]*l
        else:
            assert len(self.ratio) == l
            total = sum(self.ratio)
            self.col_widths = [int(r/total*w) for r in self.ratio]

    def get_layouts(self):
        out = []
        # print(self._rows)
        # print(self._widths)
        self._compute_col_widths()
        for row in self._rows:
            r = [TextBlock(t,width=w) for t,w in zip(row,self.col_widths)]
            out.append(HorLayout(r))
        return VerLayout(out)

    def get_image(self, **kwargs):
        return self.get_layouts().get_image()
#
#
#
if __name__ == "__main__":
    import faker

    f = faker.Faker()
#     # t = TextBlock(f.paragraph(10), 400, 0)
#     #
#     # s = t.get_string()
#
#     # img = put_text_in_box_without_break_word(f.paragraph(10), 800, font_size=20)
#     #
#     # # print(s)
#     # # x = draw_multiline_text(s,'black')
#     # img.save('x.jpg')
#     # # img = t.get_image()["image"]
#     # # cv2.imwrite('t.jpg',img)
    t = TextTable(width=1000, ratio=[2, 8])

    t.add_row(['1',f.paragraph(3)])
    t.add_row(['2', f.paragraph(3)])
    t.add_row(['3', f.paragraph(3)])
    # print(t)
    x= t.get_image()['image']
    cv2.imwrite('t.jpg',x)