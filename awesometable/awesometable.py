import re
import textwrap
from functools import reduce

import numpy as np
import prettytable
from PIL import Image, ImageDraw, ImageFont
from prettytable import ALL, FRAME
from prettytable.prettytable import _get_size, _str_block_width


from utils.ulpb import is_chinese

V_LINE_PATTERN = re.compile("[║╬╦╩╣╠╗╔╝╚]")
H_LINE_PATTERN = re.compile(r"(\n*[╔╠╚].+?[╗╣╝]\n*)")
H_SYMBOLS = "═╩╦╬╝╚╗╔"
ALL_SYMBOLS = set("║╬╦╩╣╠╗╔╝╚═╩╦╬╝╚╗╔")


class AwesomeTable(prettytable.PrettyTable):
    """可以在表格上下左右添加标题栏的AwesomeTable，获取结构化数据的字符串表示

    table_width 指定表格的字符宽度，不包含竖线
    field_names 列名
    title_pos   标题所在位置
    max_cols    最大列数
    """

    def __init__(self, rows=None, field_names=None, **kwargs):
        super().__init__(field_names, kwargs=kwargs)
        if rows:
            self.add_rows(rows)
        self.set_style(prettytable.DOUBLE_BORDER)
        self.hrules = prettytable.ALL
        self._table_width = kwargs.get("table_width", None)
        self._title_pos = kwargs.get("title_pos", "t")
        self._title = kwargs.get("title", None)
        self.wrap_func = kwargs.get("wrap_func", wrap)  # 为了向后兼容使用不同字体

    def __getitem__(self, index):
        new = AwesomeTable()
        new.field_names = self.field_names
        for attr in self._options:
            setattr(new, "_" + attr, getattr(self, "_" + attr))
        setattr(new, "_align", getattr(self, "_align"))
        if isinstance(index, slice):
            for row in self._rows[index]:
                new.add_row(row)
        elif isinstance(index, int):
            new.add_row(self._rows[index])
        else:
            raise Exception(
                f"Index {index} is invalid, must be an integer or slice")
        return new

    @property
    def title_pos(self):
        return self._title_pos

    @title_pos.setter
    def title_pos(self, pos="t"):
        """在表格的前后左右加标题框"""
        if pos in 'lrtb':
            self._title_pos = pos
        else:
            raise KeyError("%s not in lrtb")

    @property
    def table_width(self):  # 字符表格宽度
        return len(str(self.get_string().split("\n")[0]))

    @table_width.setter
    def table_width(self, val):
        self._validate_option("table_width", val)
        self._min_table_width = val
        self._table_width = val
        self._max_table_width = val

    @property
    def table_height(self):
        return len(self.get_string().split("\n"))

    @property
    def widths(self):
        return self._widths

    @widths.setter
    def widths(self, val):
        self._widths = val

    def get_string(self, **kwargs):
        options = self._get_options(kwargs)
        title = options["title"] or self._title
        if not title:
            return super().get_string(header=False)

        title_pos = self._title_pos
        if title_pos == "t":
            return super(AwesomeTable, self).get_string(header=False)

        # 无标题字符串
        self._title = False
        ss = super(AwesomeTable, self).get_string(header=False)
        self._title = title  # 代码位置很关键

        lines = ss.splitlines()
        if title_pos == "b":
            t = self._stringify_title(title, options)
            t = t + "\n" + "╚" + "═" * (len(lines[0]) - 2) + "╝"
            return _vstack(ss, t)

        h = len(lines) - 2  # 实际可用的高度
        w, _ = _get_size(title)
        vtitle = self._stringify_vertical_title(title, w, h, options,
                                                valign="m")
        if title_pos == "l":
            return _hstack(vtitle, ss)
        elif title_pos == "r":
            return _hstack(ss, vtitle)

    def _compute_table_width(self, options):
        """增加了竖线数量的统计"""
        table_width = 2 if options["vrules"] in (FRAME, ALL) else 0
        per_col_padding = sum(self._get_padding_widths(options))
        for index, fieldname in enumerate(self.field_names):
            if not options["fields"] or (
                    options["fields"] and fieldname in options["fields"]
            ):
                table_width += self._widths[index] + per_col_padding
        table_width += len(self._widths) - 1  #
        return table_width

    def _compute_widths(self, rows, options):
        """父类中成倍放大宽度并不精确，此处改为逐个增加宽度"""
        if self._widths:
            widths = self._widths

        elif options["header"]:
            widths = [_get_size(field)[0] for field in self._field_names]
        else:
            widths = len(self.field_names) * [0]

        for row in rows:
            for index, value in enumerate(row):
                fieldname = self.field_names[index]
                if fieldname in self.max_width:
                    widths[index] = max(
                        widths[index],
                        min(_get_size(value)[0], self.max_width[fieldname]),
                    )
                else:
                    widths[index] = max(widths[index], _get_size(value)[0])
                if fieldname in self.min_width:
                    widths[index] = max(widths[index],
                                        self.min_width[fieldname])
        self._widths = widths

        if self._max_table_width:
            table_width = self._compute_table_width(options)
            if table_width > self._max_table_width:
                # Shrink widths in proportion
                num = table_width - self._max_table_width

                widths = [w - num // len(widths) for w in widths]
                for w in range(num % len(widths)):
                    widths[w] -= 1
                self._widths = widths
        if self._min_table_width or options["title"]:
            if options["title"]:
                title_width = len(options["title"]) + sum(
                    self._get_padding_widths(options)
                )
                if options["vrules"] in (FRAME, ALL):
                    title_width += 2
            else:
                title_width = 0
            min_table_width = self.min_table_width or 0
            min_width = max(title_width, min_table_width)
            table_width = self._compute_table_width(options)
            if table_width < min_width:
                num = min_width - table_width
                widths = [w + num // len(widths) for w in widths]
                for w in range(num % len(widths)):
                    widths[w] += 1
                self._widths = widths

    def _stringify_vertical_title(self, title, width, height, options,
                                  valign="m"):
        lines = title.split("\n")  # 可以包含换行
        new_lines = []
        for line in lines:
            if _str_block_width(line) > width:  # 如果元素宽度大于计算出来的宽度
                line = self.wrap_func(line, width)  # 重新包装
            new_lines.append(line)
        lines = new_lines
        value = "\n".join(lines)

        row_height = height

        bits = []
        lpad, rpad = self._get_padding_widths(options)
        for y in range(0, row_height):
            bits.append([])
            if options["border"]:
                if options["vrules"] in (ALL, FRAME):
                    bits[y].append(self.vertical_char)
                else:
                    bits[y].append(" ")

        # valign = self._valign[field]
        lines = value.split("\n")
        d_height = row_height - len(lines)  # 空行的高度

        if d_height:
            if valign == "m":  # 居中
                lines = (
                        [""] * int(d_height / 2)
                        + lines
                        + [""] * (d_height - int(d_height / 2))
                )
            elif valign == "b":
                lines = [""] * d_height + lines
            else:
                lines = lines + [" " * width] * d_height
        y = 0
        for line in lines:
            bits[y].append(
                " " * lpad + self._justify(line, width, "m") + " " * rpad
                # 中文字符x2
            )
            if options["border"]:
                if options["vrules"] == ALL:
                    bits[y].append(self.vertical_char)
                else:
                    bits[y].append(" ")
            y += 1

        for y in range(0, row_height):
            if options["border"] and options["vrules"] == FRAME:
                bits[y].pop()
                bits[y].append(options["vertical_char"])

        for y in range(0, row_height):
            bits[y] = "".join(bits[y])

        firstline = [options["top_left_junction_char"]]
        firstline.extend([options["horizontal_char"]] * (width + 2))
        firstline.append(options["top_right_junction_char"])
        firstline = "".join(firstline)

        endline = [options["bottom_left_junction_char"]]
        endline.extend([options["horizontal_char"]] * (width + 2))
        endline.append(options["bottom_right_junction_char"])
        endline = "".join(endline)

        bits.insert(0, firstline)
        bits.append(endline)

        return "\n".join(bits)

    def _stringify_row(self, row, options, hrule):
        for (index, field, value, width) in zip(
                range(0, len(row)), self._field_names, row, self._widths
        ):
            # Enforce max widths
            lines = value.split("\n")
            new_lines = []
            for line in lines:
                if _str_block_width(line) > width:
                    line = self.wrap_func(line, width)
                new_lines.append(line)
            lines = new_lines
            value = "\n".join(lines)
            row[index] = value

        row_height = 0
        for c in row:
            h = _get_size(c)[1]
            if h > row_height:
                row_height = h

        bits = []
        lpad, rpad = self._get_padding_widths(options)
        for y in range(0, row_height):
            bits.append([])
            if options["border"]:
                if options["vrules"] in (ALL, FRAME):
                    bits[y].append(self.vertical_char)
                else:
                    bits[y].append(" ")

        for (field, value, width) in zip(self._field_names, row, self._widths):

            valign = self._valign[field]
            lines = value.split("\n")
            d_height = row_height - len(lines)
            if d_height:
                if valign == "m":
                    lines = (
                            [""] * int(d_height / 2)
                            + lines
                            + [""] * (d_height - int(d_height / 2))
                    )
                elif valign == "b":
                    lines = [""] * d_height + lines
                else:
                    lines = lines + [""] * d_height

            y = 0
            for line in lines:
                if options["fields"] and field not in options["fields"]:
                    continue

                bits[y].append(
                    " " * lpad
                    + self._justify(line, width, self._align[field])
                    + " " * rpad
                )
                if options["border"]:
                    if options["vrules"] == ALL:
                        bits[y].append(self.vertical_char)
                    else:
                        bits[y].append(" ")
                y += 1

        # If vrules is FRAME, then we just appended a space at the end
        # of the last field, when we really want a vertical character
        for y in range(0, row_height):
            if options["border"] and options["vrules"] == FRAME:
                bits[y].pop()
                bits[y].append(options["vertical_char"])

        if options["border"] and options["hrules"] == ALL:
            bits[row_height - 1].append("\n")
            bits[row_height - 1].append(hrule)

        for y in range(0, row_height):
            bits[y] = "".join(bits[y])

        return "\n".join(bits)

    def __str__(self):
        return self.get_string()

    def get_image(self, **kwargs):
        return table2image(str(self), **kwargs)

    def init_attr(self):
        """
        text_layer 文本层
        char_width_layer  字符串宽度层
        char_height_layer 字符串高度层
        char_color_layer  字符串颜色层
        char_fontsize_layer 字号层
        char_font_layer 字体层
        padding_layer 四组填充
        border_layer 边框层
        """
        rows = self._rows
        w = len(rows[0])
        h = len(rows)
        self.text_layer = np.chararray(
            (h, w), unicode=True, itemsize=50
        )  # 每个单元格的文字作为一层
        self.char_width_layer = np.ndarray((h, w), np.int32)  # 字符串宽度层
        self.char_height_layer = np.ndarray((h, w), np.int32)  # 字符串高度层
        self.char_color_layer = np.ndarray((h, w, 3), np.uint8)  # 字符串颜色层
        self.char_fontsize_layer = np.ndarray((h, w), np.int32)  # 字号层
        self.padding_layer = np.ndarray((h, w, 4), np.int8)  # 四边填充层
        self.border_width_layer = np.ndarray((h, w, 4), np.int8)  # 边框宽度层

        self.border_width_layer[:] = 1
        self.padding_layer[:] = 2
        self.char_color_layer[:] = 255
        self.char_fontsize_layer[:] = 24
        self.title_width = None
        self.title_height = None
        # 计算各个单元格子的宽和高

    def _compute_box_size(self):
        rows = self._rows
        w = len(rows[0])
        h = len(rows)
        for i in range(h):
            for j in range(w):
                self.text_layer[i, j] = rows[i][j]
                _w, _h = _get_size(rows[i][j])
                self.char_width_layer[i, j] = _w
                self.char_height_layer[i, j] = _h

        self.box_width_layer = (
                np.multiply(self.char_width_layer,
                            self.char_fontsize_layer // 2)
                + self.padding_layer[:, :, 0]
                + self.padding_layer[:, :, 2]
        )
        self.box_height_layer = (
                np.multiply(self.char_height_layer, self.char_fontsize_layer)
                + self.padding_layer[:, :, 1]
                + self.padding_layer[:, :, 3]
        )

        self.box_height_layer = np.max(self.box_height_layer, axis=1)
        self.box_width_layer = np.max(self.box_width_layer, axis=0)

    def scale(self, xratio, yratio=1.0):
        self.box_width_layer = np.int32(self.box_width_layer * xratio)

        self.title_width = (
            round(self.title_width * xratio) if self.title_width else None
        )
        self.title_height = (
            round(self.title_height * yratio) if self.title_height else None
        )

        self.box_height_layer = np.int32(self.box_height_layer * yratio)
        # self.char_fontsize_layer = np.int32(self.char_fontsize_layer * yratio)

    def get_table_image(self):
        """直接从表格生成图片而不是从字符串生成，渲染成图"""
        self.init_attr()
        self._compute_box_size()
        font_path = "static/fonts/simfang.ttf"
        rows = self._rows
        w = len(rows[0])
        h = len(rows)
        arrays = [[None for j in range(w)] for i in range(h)]
        for i in range(h):
            for j in range(w):
                print(i, j)
                text = self.text_layer[i, j]
                width, height = self.box_width_layer[j], self.box_height_layer[
                    i]
                border = self.border_width_layer[i, j, 0]

                bg = Image.new(
                    "RGB", (width, height),
                    tuple(self.char_color_layer[i, j].tolist())
                )

                bg_draw = ImageDraw.Draw(bg)
                font = ImageFont.truetype(
                    font_path, self.char_fontsize_layer[i, j], encoding="utf-8"
                )
                bg_draw.multiline_text(
                    (width // 2, height // 2),
                    text,
                    "black",
                    font,
                    anchor="mm",
                    align="center",
                )
                bg_draw.line((0, 0) + (width, 0), fill="black", width=border)
                bg_draw.line((0, 0) + (0, height), fill="black", width=border)

                arrays[i][j] = np.array(bg)

        row_imgs = []
        for row in arrays:
            row_imgs.append(np.hstack(row))
        table_img = np.vstack(row_imgs)

        # self.table_image_width = np.sum(self.box_width_layer)
        # self.table_image_height = np.sum(self.box_height_layer)

        if self.title:
            text = self.title
            title_font_size = np.max(self.char_fontsize_layer)
            font = ImageFont.truetype(font_path, title_font_size,
                                      encoding="utf-8")
            size = font.getsize_multiline(text)

            if self.title_pos in "lr":
                ht = np.sum(self.box_height_layer)
                wt = self.title_width or size[0] + title_font_size
            else:
                wt = np.sum(self.box_width_layer)
                ht = self.title_height or size[1] + title_font_size

            bg = Image.new("RGB", (wt, ht), "white")
            bg_draw = ImageDraw.Draw(bg)
            bg_draw.multiline_text(
                (wt // 2, ht // 2), text, "black", font, anchor="mm",
                align="center"
            )

            bg_draw.rectangle((0, 0) + (wt, ht), outline="black", width=1)
            title_img = np.array(bg)
            self.title_height, self.title_width = title_img.shape[:2]

            if self.title_pos == "l":
                return np.hstack([title_img, table_img])
            elif self.title_pos == "r":
                return np.hstack([table_img, title_img])
            elif self.title_pos == "t":
                return np.vstack([title_img, table_img])
            elif self.title_pos == "b":
                return np.hstack([table_img, title_img])
        return table_img

    def vstack(self, other):
        s = self.get_table_image()
        o = other.get_table_image()
        print(s.shape, o.shape)
        hs, ws = s.shape[:2]
        ho, wo = o.shape[:2]
        if ws < wo:
            self.scale(xratio=wo / ws)
        else:
            other.scale(xratio=ws / wo)

        s = self.get_table_image()
        o = other.get_table_image()
        print(s.shape, o.shape)
        return np.vstack([s, o])

    def hstack(self, other):
        s = self.get_table_image()
        o = other.get_table_image()
        print(s.shape, o.shape)
        hs, ws = s.shape[:2]
        ho, wo = o.shape[:2]

        if hs < ho:
            self.scale(xratio=1, yratio=ho / hs)
        else:
            other.scale(xratio=1, yratio=hs / ho)

        s = self.get_table_image()
        o = other.get_table_image()
        print(s.shape, o.shape)
        return np.hstack([o, s])


class MultiTable(object):
    """多表格类"""

    def __init__(self, tables):
        self._tables = tables
        self._table_width = 0

    def add_table(self, table):
        assert isinstance(table, AwesomeTable)
        self._tables.append(table)

    @property
    def table_width(self):
        return self._table_width

    @table_width.setter
    def table_width(self, val):
        self._table_width = val
        for table in self._tables:
            table.table_width = val

    def get_string(self):
        if self._table_width == 0:
            self.table_width = max([t._table_width for t in self._tables])
        return vstack(self._tables)

    def __str__(self):
        return self.get_string()


def paginate(table, lines_per_page=40):
    """分页算法
    1.保证按行分割，行内有换行不会被分开
    2.必须分割时另起一页
    3.修复分割线
    """
    lct = 0
    lines = re.split(H_LINE_PATTERN, str(table))
    out = ""
    for line in lines:
        if not line:
            continue
        if line[0] == "║":
            if lct >= lines_per_page:
                yield out
                out = out.splitlines()[-1] + "\n" + line  # 封顶
                lct = len(line.splitlines())
            else:
                out += line
                lct += len(line.splitlines())
        else:
            out += line
    yield out


def clear_symbols(s):
    o = ""
    for c in s:
        if c in ALL_SYMBOLS:
            o += " "
        else:
            o += c
    return o


def _align_cell(ct, align):
    nc = ct.strip()
    lpad = (len(ct) - len(nc)) // 2
    rpad = len(ct) - len(nc) - lpad
    if align == "c":
        nt = (lpad * " ") + nc + (rpad * " ")
    elif align == "l":
        nt = " " + nc + ((lpad + rpad - 1) * " ")
    elif align == "r":
        nt = ((lpad + rpad - 1) * " ") + nc + " "
    else:
        raise KeyError
    return nt


def set_align(t, cno, align, rno=None):
    # 精细调整表格列内对齐方式
    lines = str(t).splitlines()
    if rno is None:
        out = []
        for line in lines:
            if "═" in line:
                out.append(line)
            else:
                cells = re.split(V_LINE_PATTERN, line)[1:-1]
                try:
                    ct = cells[cno]
                except:
                    continue
                nt = _align_cell(ct, align)
                line = line.replace(ct, nt)
                out.append(line)
        return "\n".join(out)
    else:
        line = lines[2 * rno + 1]
        cells = re.split(V_LINE_PATTERN, line)[1:-1]
        ct = cells[cno]
        nt = _align_cell(ct, align)
        lines[2 * rno + 1] = line.replace(ct, nt)
        return "\n".join(lines)


def merge_row(t, rno):
    # 合并同一行的cells
    lines = str(t).splitlines()
    rline = lines[2 * rno + 1]

    nline = "║" + rline.replace("║", " ")[1:-1] + "║"
    lines[2 * rno + 1] = nline
    return "\n".join(lines)


def remove_hlines(t, start=2, end=-1, keepblank=True):
    """移除中间的横线"""
    lines = str(t).splitlines()
    if keepblank:
        lines[start:end:2] = [
            "║" + (len(l) - 2) * " " + "║" for l in lines[start:end:2]
        ]
    else:
        del lines[start:end:2]
    return "\n".join(lines)


def add_width(self, num=1):
    """表格横向拉伸"""
    ss = str(self)
    lines = ss.splitlines()
    newlines = []
    for line in lines:
        try:
            ch = line[-2]
            if ch == "═":
                # newline = line[0:-1] + ch * (num) + line[-1]
                newline = line[0] + line[1:-1] + line[-2] * (num) + line[-1]
            elif "║" in line:
                x = line.rsplit("║", 2)
                newline = (
                        x[0] + "║" + " " * (num // 2) + x[1] + " " * (
                        num - num // 2) + "║"
                )
            else:
                newline = line
        except IndexError:
            newline = line
        newlines.append(newline)

    return "\n".join(newlines)


def add_newline(self, num=1, align="t"):
    """纵向拉伸,直接加到末尾"""
    idx = -1
    ss = str(self)
    scale_lines = ss.splitlines()
    if align == "t":
        idx = -1
    elif align == "b":
        idx = 0

    end_line = scale_lines[idx]
    insect_line = []
    for c in end_line:
        if c == "═":
            insect_line.append(" ")
        else:
            insect_line.append("║")
    insect_line = "".join(insect_line)

    if align == "t":
        for i in range(num):
            scale_lines.insert(idx, insect_line)
    else:
        for i in range(num):
            scale_lines.insert(1, insect_line)

    return "\n".join(scale_lines)


def _hstack(self, other, merged=True, space=0, align="t"):
    """表格字符横向拼接"""
    ss = str(self)
    so = str(other)
    hss = len(ss.splitlines())
    hso = len(so.splitlines())

    if hss > hso:
        so = add_newline(so, hss - hso, align)
    elif hss < hso:
        ss = add_newline(ss, hso - hss, align)
    else:
        pass
    lss = ss.splitlines()
    lso = so.splitlines()
    new_lines = []
    for lno in range(len(lss)):
        e = lss[lno][-1]
        s = lso[lno][0]
        if e == s == "║":
            ret = "║"
        elif e == "╗" and s == "╔":
            ret = "╦"

        elif e == "╣" and s == "║":
            ret = "╣"

        elif e == "╣" and s == "╠":
            ret = "╬"

        elif e == "║" and s == "╠":

            ret = "╠"

        elif e == "╝" and s == "╚":
            ret = "╩"
        else:
            print(self, other)
            raise Exception("Unmatch symbol %s and %s" % (e, s))
        if merged:
            new_lines.append(lss[lno][:-1] + ret + lso[lno][1:])
        else:
            new_lines.append(lss[lno] + " " * space + lso[lno])

    return "\n".join(new_lines)


def _vstack(self, other, merged=True):
    """表格字符纵向拼接"""
    ss = str(self)
    so = str(other)
    hss = len(ss.splitlines()[0])
    hso = len(so.splitlines()[0])
    if hss > hso:
        so = add_width(so, hss - hso)
    elif hss < hso:
        ss = add_width(ss, hso - hss)
    else:
        pass
    if ss.splitlines()[-1][-1] != "╝" or so[0] != "╔":  # 这种情况下至少有一方不是表格，直接叠加
        return ss + "\n" + so

    if merged:
        ens = ss.splitlines()[-1]
        suc = so.splitlines()[0]

        ret = []
        for e, s in zip(ens, suc):
            if e == s == "═":
                ret.append(e)
            elif e == "╚" and s == "╔":
                ret.append("╠")
            elif e == "╝" and s == "╗":
                ret.append("╣")
            elif e == "╩" and s == "╦":
                ret.append("╬")
            elif e == "╩" and s == "═":
                ret.append("╩")
            elif e == "═" and s == "╦":
                ret.append("╦")
            elif e == "═" and s == "╗":
                ret.append("╗")
            else:
                print(e, s)
                print(self)
                print(other)
                raise Exception("unmatch")
        midline = "".join(ret)
        new_lines = ss.splitlines()[:-1] + [midline] + so.splitlines()[1:]
        return "\n".join(new_lines)
    else:
        return ss + "\n\n" + so


def hstack(tables, other=None):
    if isinstance(tables, list) and other is None:
        return reduce(_hstack, tables)
    else:
        return _hstack(tables, other)


def vstack(tables, other=None):
    if isinstance(tables, list) and other is None:
        return reduce(_vstack, tables)
    else:
        return _vstack(tables, other)


def stack(tables):
    return vstack([hstack(table) for table in tables])


def wrap(line, width):
    """考虑了中文宽度和字母宽度不一样"""
    if not any(is_chinese(c) for c in line):  # 没有中文则保持原样
        return textwrap.fill(line, width)

    lines = []
    n = ""
    for ch in line:
        n += ch
        if _str_block_width(n) == width:
            lines.append(n)
            n = ""
        elif _str_block_width(n) > width:
            lines.append(n[:-1])
            n = n[-1]
        else:
            continue
    if n:
        lines.append(n)
    return "\n".join(lines)


if __name__ == "__main__":
    # jsonobject = {'本年金额':{'归属':{'a':1,'b':2,'v':3,'d':4,'e':5,'f':6},'少数':1,'所有':2},
    #               '上年金额': {'归属':{'a':1,'b':2,'v':3,'d':4,'e':5,'f':6}, '少数': 1,
    #                        '所有': 2},}
    from awesometable.table2pdf import render_pdf
    from image import table2image
    test = [
        "项目",
        ["本年金额", [["gv", [2, 3, 4, [2, [3, 4]], 6, 7]], "少数", "所有者"]],
    ]
    from converter import from_list
    tab = from_list(test, False)

    data = render_pdf(table2image(tab),'x.pdf')

    # cv2.imwrite('tmp.jpg',data['image'])

    # print(tab)
    # lines = tab.splitlines()
    # vpat = re.compile("[║╬╦╩╣╠╗╔╝╚]")
    # for lno,line in enumerate(lines):
    #     cells = re.split(vpat,line)[1:-1]
    #     for cno,cell in enumerate(cells):
    #         left = sum(len(c)+1 for c in cells[:cno])+1
    #         if '═' not in cell:
    #             text = cell.strip()
    #             right = left + len(cell)-1
    #             top = lno - 1
    #             bottom = lno + 1
    #
    #             while lines[top][left] != '═':
    #                 top -= 1
    #
    #             while lines[bottom][left] != '═':
    #                 bottom += 1
    #             print(text,left,right,top,bottom)

    # t2 = AwesomeTable()
    # t2.add_row(['货物名称', '包装', '件数', '重量', '运费', '保险费', '送货费', '其它费用', '合计'])
    # t2.add_row([str(random.randint(100,1000)) for i in range(9)])
    # t2.add_row([str(random.randint(100,1000)) for i in range(9)])
    # # print(t2)
    #
    # t3 = AwesomeTable(vrules=FRAME)
    # t3.add_row(
    #     ['合计金额（大写）：', '壹', '万', '贰', '仟', '叁', '佰', '肆', '拾', '伍', '元', '陆', '角'])
    #
    # t4 = AwesomeTable()
    # t4.add_row(['现付', '提付', '欠付', '回单\n付追中', '月结'])
    # t4.add_row(['是', '否', '否', '否', '否'])
    # t4.title = '付款方式'
    # t4.title_pos = 't'
    # t4.init_attr()
    # cvshow(t4.get_table_image())

    #
    # # t4.init_attr()
    # # img = t4.get_table_image()
    # # cvshow(img)
    # # t4.scale(1.5,0.8)
    # # img = t4.get_table_image()
    # # cvshow(img)
    #
    # t1 = AwesomeTable()
    # t1.add_row(['送货', '自提'])
    # t1.add_row(['是', '否'])
    # t1.title = '提货方式'
    #
    #
    # s1 = t1.get_string()
    # t1.title_pos = 't'
    # print(t1)
    # s2 = t1.get_string()
    # t1.title_pos = 'r'
    # print(t1)
    # s3 = t1.get_string()
    # t1.title_pos = 'b'
    # print(t1)
    # s4 = t1.get_string()
    # # t1._title = None
    # # print(t1)
    # # s5 = t1.get_string()
    # t1.title_pos = 'l'
    # print(t1)
    #
    # print(vstack([s1,s2]))
    # print(hstack([s1,s2]))
    #
    # t5 = AwesomeTable()
    # t5.add_row(['托运人签字：', '张三', '提货人签字：', '李四'])
    #
    # # t5.render()
    #
    # t6 = AwesomeTable()
    # t6.add_row(['备注：', '没有什么需要备注的'])
    #
    # t = AwesomeTable()
    # t.add_row(['托运人', '张三丰', '电话', '13333333333', '单位地址', '江苏省润和股份有限公司'])
    # t.add_row(['收货人', '李四光', '电话', '14444444444', '单位地址', '江苏省南京市东南大学'])
    # t.title = '人物信息'
    # t.title_pos = 'l'

    # g = TableGrouper([t,t1,t2,t3,t4,t5,t6])
    # print(g)
    # g = stack([[t], [t2], [t3], [t4, t1], [t5], [t6]])
    # print(g)
    # for i in range(10):
    #     img = table2image(g)
    #     img.save('./data/example_%d.jpg'%i)

    # t.get_image()
    # print(g)
    # img = table2image(g,font_size=20)

    # img.save('./tmp1.jpg')
    # img.save('./data/example_check.jpg')
    # c = 0
    #
    # for i in [t, t1, t2, t3, t4, t5, t6]:
    #     i.init_attr()
    # # cvshow(t.vstack(t1))
    # cvshow(t.hstack(t2))
    # cvshow(t.vstack(t2)) # 元整函数会导致图片宽度不对齐
    # #     img = i.get_table_image()
    # #     cvshow(img)
    # #     # cv2.imwrite('%d.jpg'%c,img)
    # #     c+=1
