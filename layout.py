# __author__ = "arry lee"
# 2022-2-21 17:37:31
# LayoutTable 是用于管理布局的表格

import textwrap
from abc import ABCMeta, abstractmethod

import cv2
import numpy as np
import prettytable
from PIL import Image, ImageDraw, ImageFont

from awesometable import AwesomeTable, from_str, hstack, vstack


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

    @abstractmethod
    def get_image(self, offset):
        return NotImplemented

    def extend(self, obj):
        if hasattr(obj, "get_image"):
            self.layouts.extend(obj)
        else:
            raise ValueError("Not Layout or Table")


class HorLayout(AbstractTable):
    """水平方向布局的抽象
    任何实现了 get_image 方法和 table_width 属性的类表格，
    均可作为布局管理的 layouts列表的子元素，包括布局自身
    """

    def __init__(self, layouts=None, widths=None):
        super().__init__()
        self.layouts = layouts or []
        if isinstance(widths, int):
            self._widths = [widths] * len(self.layouts)
        elif isinstance(widths, list):
            self._widths = widths
        else:
            self._widths = [x.table_width for x in self.layouts]
        self._table_width = sum(x + 1 for x in self._widths) - 1
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

    def get_image(self, offset=0):
        col = []
        out = {}
        for lot, w in zip(self.layouts, self._widths):
            lot.table_width = w
            imgc = lot.get_image()
            col.append(imgc)
        # 计算背景尺寸
        h = max(x["image"].shape[0] for x in col) + offset * 2
        w = sum(x["image"].shape[1] for x in col) + offset * 2
        img = np.ones((h, w, 3), np.uint8) * 255
        x = offset
        y = offset
        for data in col:
            h, w = data["image"].shape[:2]
            img[y: y + h, x: x + w] = data["image"]
            data["points"] = (np.array(data["points"]) + (x, y)).tolist()
            if not out:
                out = data
            else:
                out["image"] = img
                out["label"].extend(data["label"])
                out["points"].extend(data["points"])
            x += w
        return out


class VerLayout(AbstractTable):
    """输入二维列表，输出布局"""

    def __init__(self, layouts=None, widths=None):
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

    def get_image(self, offset=0):
        row = []
        out = {}
        for lot, w in zip(self.layouts, self._widths):
            lot.table_width = w
            imgc = lot.get_image()
            assert isinstance(imgc, dict)
            row.append(imgc)

        h = sum(x["image"].shape[0] for x in row) + offset * 2
        w = max(x["image"].shape[1] for x in row) + offset * 2
        img = np.ones((h, w, 3), np.uint8) * 255
        x = offset
        y = offset
        for data in row:
            h, w = data["image"].shape[:2]
            img[y: y + h, x: x + w] = data["image"]
            data["points"] = (np.array(data["points"]) + (x, y)).tolist()
            if not out:
                out = data
            else:
                out["image"] = img
                out["label"].extend(data["label"])
                out["points"].extend(data["points"])
            y += h
        return out


class TextTable(AwesomeTable):
    """文本框 内自动排版
    英文字体大多都是非等宽字体，如果按行左对齐则右边参差补齐
    """

    def __init__(self, string, table_width=None, indent=0):
        super().__init__()
        self.add_row([" " * indent + string])
        self.align = "l"
        self.table_width = table_width
        self._padding_width = 0
        self._left_padding_width = 0
        self._right_padding_width = 0

    def get_image(self, **kwargs):
        kwargs["vrules"] = "NONE"
        kwargs["hrules"] = "NONE"
        kwargs["font_path"] = "arial.ttf"
        return super(TextTable, self).get_image(**kwargs)

    def hide_outlines(self):
        self._horizontal_char = " "
        self._vertical_char = " "
        self._junction_char = " "
        self._top_junction_char = " "
        self._bottom_junction_char = " "
        self._right_junction_char = " "
        self._left_junction_char = " "
        self._top_right_junction_char = " "
        self._top_left_junction_char = " "
        self._bottom_right_junction_char = " "
        self._bottom_left_junction_char = " "


class TextBlock(object):
    def __init__(self, text, width, indent=0, **kwargs):
        self._text = text
        self.indent = indent
        self._table_width = width
        self.align = kwargs.get("align", "l")
        self.font_size = kwargs.get("font_size", 20)

    @property
    def text(self):
        return " " * self.indent + self._text

    @property
    def wrap_text(self):
        return textwrap.wrap(self.text, self._table_width)

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
            return self.double_end_align(s, self._table_width)
        else:
            return put_text_in_box(self.text, self._table_width * 10)[0]

    def get_image(self, font_path="arial.ttf", font_size=20):
        s, img,boxes = put_text_in_box(
            self.text,
            self._table_width * font_size // 2,
            font_size=font_size,
            font_path=font_path,
        )

        bg = Image.new("RGB", (img.width + font_size, img.height + font_size),
                       "white")
        bg.paste(img, (font_size // 2, font_size // 2))
        points = []
        for box in boxes:
            points.append([box[0]+font_size // 2, box[1]+font_size // 2])
            points.append([box[2]+font_size // 2, box[1]+font_size // 2])
            points.append([box[2]+font_size // 2, box[3]+font_size // 2])
            points.append([box[0]+font_size // 2, box[3]+font_size // 2])

        return {
            "image" :cv2.cvtColor(np.asarray(bg, np.uint8), cv2.COLOR_RGB2BGR),
            "points":points,
            "label" :["text@"+l for l in s.splitlines()],
        }


def draw_multiline_text(xy, text, fill, font_path="arial.ttf", font_size=20):
    """通过像素偏移实现两端对齐"""
    text_list = text.splitlines()
    font = ImageFont.truetype(font_path, font_size)
    width = max(font.getsize(t)[0] for t in text_list) + font_size * 5
    img = Image.new("RGB", (width, font_size * len(text_list)), "white")
    draw = ImageDraw.Draw(img)
    x, y = xy
    max_width = 0
    for t in text_list[:-1]:
        w = font.getsize(t)[0]
        pix = width - w
        chars = len(t) - 1
        n = pix // chars
        m = pix % chars
        offsets = [n] * chars
        for i in range(m):
            offsets[i] += 1
        offsets.append(0)

        for c, b in zip(t, offsets):
            draw.text((x, y), c, fill, font)
            w = font.getsize(c)[0]
            x += w + b
        max_width = max(max_width, x)
        x = 0
        y += font_size
    draw.text((x, y), text_list[-1], fill, font)
    height = y + font_size
    # img = img.crop((0,0,max_width,height))
    img.show()
    return img


def put_text_in_box(
        text, width, fill="black", font_path="arial.ttf", font_size=20,
        line_pad=2
):
    # 不硬换行，软换行
    font = ImageFont.truetype(font_path, font_size)
    img = Image.new("RGB", (width, width), "white")
    draw = ImageDraw.Draw(img)

    space_width = font.getsize(" ")[0]
    indent = 0
    for i in text:
        if i.isspace():
            indent += 1
        else:
            break
    words = text.split()
    words[0] = " " * indent + words[0]
    lines = []
    line = ""
    boxes = []
    x, y = 0, 0
    for word in words:
        bbox = draw.textbbox((x, y), word, font)
        if bbox[2] < width:
            draw.text((x, y), word + " ", fill, font)
            line += word + " "
            x = bbox[2] + space_width
        elif bbox[2] > width:
            for i, c in enumerate(word):
                bbox = draw.textbbox((x, y), c, font)
                if bbox[2] < width - space_width:
                    draw.text((x, y), c, fill, font)
                    line += c
                    x = bbox[2]
                else:
                    if i > 0:
                        draw.text((x, y), "-", fill, font)
                        line += "-"
                    lines.append(line)
                    boxes.append((0,y,width,y+font_size))
                    x = 0
                    y += font_size + line_pad
                    line = word[i:] + " "
                    draw.text((x, y), line, fill, font)
                    x = draw.textbbox((x, y), line, font)[2]
                    break
        else:
            draw.text((x, y), word, fill, font)
            line += word
            lines.append(line)
            boxes.append((0, y, width, y + font_size))
            line = ""
            x = 0
            y += font_size + line_pad

    lines.append(line)
    bbox = draw.textbbox((0, y), line, font)
    boxes.append(bbox)
    height = y + font_size + line_pad
    img = img.crop((0, 0, width, height))
    # points = []
    # for box in boxes:
    #     points.append([box[0], box[1]])
    #     points.append([box[2], box[1]])
    #     points.append([box[2], box[3]])
    #     points.append([box[0], box[3]])
    # label = ["text@"+l for l in lines]

    return "\n".join(lines), img,boxes


def from_list(ls, t2b=True, w=None):
    if t2b:
        rows = []
        for value in ls:
            if isinstance(value, list):
                tv = from_list(value, not t2b, w)
            elif isinstance(value, AwesomeTable):
                value.table_width = w
                tv = AwesomeTable()
                tv.add_row([value.get_string()])
            else:
                tv = from_str(value, w + 2)

            rows.append(tv)
        return vstack(rows)
    else:
        cols = []
        for value in ls:
            if isinstance(value, list):
                tv = from_list(value, not t2b, w)
            elif isinstance(value, AwesomeTable):
                value.table_width = w
                tv = AwesomeTable()
                tv.add_row([value.get_string()])
            else:
                tv = from_str(value, w + 2)
            cols.append(tv)
        return hstack(cols)


if __name__ == "__main__":
    import faker

    f = faker.Faker()
    t = TextBlock(f.paragraph(10), 38, 4)
    s = t.get_string()
    print(s)
    img = t.get_image(font_path="arial.ttf")["image"]
    img.show()
