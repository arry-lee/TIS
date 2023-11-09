"""
awesometable create text table in simple way
"""
import re
from functools import partial, reduce

import prettytable
import wcwidth
from prettytable import ALL, FRAME

V_LINE_PATTERN = re.compile("[║╬╦╩╣╠╗╔╝╚]")
H_LINE_PATTERN = re.compile(r"(\n*[╔╠╚].+?[╗╣╝]\n*)")
H_SYMBOLS = "═╩╦╬╝╚╗╔"
ALL_SYMBOLS = set("║╬╦╩╣╠╗╔╝╚═╩╦╬╝╚╗╔")
_re = re.compile(r"\033\[[0-9;]*m|\033\(B")


def get_size(text):
    """
    :param text: str
    :return: tuple[int,int]
    """
    lines = text.split("\n")
    height = len(lines)
    width = max(str_block_width(line) for line in lines)
    return width, height


def remove_invisible_chars(chars):
    """移除所有不可见字符，除\n外"""
    text = ''
    for char in chars:
        if char != '\n' and not char.isprintable():
            text += ''
        else:
            text += char
    return text


def remove_tone_chars(chars):
    text = ''
    for char in chars:
        if wcwidth.wcswidth(_re.sub("", char)) == 0:
            text += ''
        else:
            text += char
    return text


def clean_chars(chars):
    return remove_invisible_chars(remove_tone_chars(chars))


def str_block_width(val):
    """文本形式宽度"""
    val = remove_invisible_chars(val)
    val = remove_tone_chars(val)
    return wcwidth.wcswidth(_re.sub("", val))


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
        """标题位置"""
        return self._title_pos
    
    @title_pos.setter
    def title_pos(self, pos="t"):
        """在表格的前后左右加标题框"""
        if pos in "lrtb":
            self._title_pos = pos
        else:
            raise KeyError("%s not in lrtb")
    
    @property
    def table_width(self):
        """字符表格宽度"""
        return len(str(self.get_string().split("\n")[0]))
    
    @table_width.setter
    def table_width(self, val):
        self._validate_option("table_width", val)
        self._min_table_width = val
        self._table_width = val
        self._max_table_width = val
    
    @property
    def table_height(self):
        """字符表格高度"""
        return len(self.get_string().split("\n"))
    
    @property
    def widths(self):
        """字符表格列宽"""
        return self._widths
    
    @widths.setter
    def widths(self, val):
        self._widths = val
    
    def get_string(self, **kwargs):
        """字符串表示"""
        options = self._get_options(kwargs)
        title = options["title"] or self._title
        if not title:
            return super().get_string(header=False)
        
        title_pos = self._title_pos
        if title_pos == "t":
            return super().get_string(header=False)
        
        self._title = False  # 无标题字符串
        sos = super().get_string(header=False)
        self._title = title  # 代码位置很关键
        
        lines = sos.splitlines()
        if title_pos == "b":
            tab = self._stringify_title(title, options)
            tab = tab + "\n" + "╚" + "═" * (len(lines[0]) - 2) + "╝"
            return _vstack(sos, tab)
        
        height = len(lines) - 2  # 实际可用的高度
        width, _ = get_size(title)
        vtitle = self._stringify_vertical_title(
            title, width, height, options, valign="m"
        )
        if title_pos == "l":
            return _hstack(vtitle, sos)
        if title_pos == "r":
            return _hstack(sos, vtitle)
    
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
            widths = [get_size(field)[0] for field in self._field_names]
        else:
            widths = len(self.field_names) * [0]
        for row in rows:
            for index, value in enumerate(row):
                fieldname = self.field_names[index]
                if fieldname in self.max_width:
                    widths[index] = max(
                        widths[index],
                        min(get_size(value)[0], self.max_width[fieldname]),
                    )
                else:
                    widths[index] = max(widths[index], get_size(value)[0])
                if fieldname in self.min_width:
                    widths[index] = max(widths[index],
                                        self.min_width[fieldname])
        self._widths = widths
        
        if self._max_table_width:
            table_width = self._compute_table_width(options)
            if table_width > self._max_table_width:
                # Shrink widths in proportion
                num = table_width - self._max_table_width
                widths = [wid - num // len(widths) for wid in widths]
                for i in range(num % len(widths)):
                    widths[i] -= 1
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
                for i in range(num % len(widths)):
                    widths[i] += 1
                self._widths = widths
    
    def _stringify_vertical_title(self, title, width, height, options,
                                  valign="m"):
        lines = title.split("\n")  # 可以包含换行
        new_lines = []
        for line in lines:
            if str_block_width(line) > width:  # 如果元素宽度大于计算出来的宽度
                line = self.wrap_func(line, width)  # 重新包装
            new_lines.append(line)
        lines = new_lines
        value = "\n".join(lines)
        
        row_height = height
        
        bits = []
        lpad, rpad = self._get_padding_widths(options)
        for i in range(0, row_height):
            bits.append([])
            if options["border"]:
                if options["vrules"] in (ALL, FRAME):
                    bits[i].append(self.vertical_char)
                else:
                    bits[i].append(" ")
        
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
        i = 0
        for line in lines:
            bits[i].append(
                " " * lpad + self._justify(line, width, "m") + " " * rpad)
            if options["border"]:
                if options["vrules"] == ALL:
                    bits[i].append(self.vertical_char)
                else:
                    bits[i].append(" ")
            i += 1
        
        for i in range(0, row_height):
            if options["border"] and options["vrules"] == FRAME:
                bits[i].pop()
                bits[i].append(options["vertical_char"])
        
        for i in range(0, row_height):
            bits[i] = "".join(bits[i])
        
        first_line = [options["top_left_junction_char"]]
        first_line.extend([options["horizontal_char"]] * (width + 2))
        first_line.append(options["top_right_junction_char"])
        first_line = "".join(first_line)
        
        end_line = [options["bottom_left_junction_char"]]
        end_line.extend([options["horizontal_char"]] * (width + 2))
        end_line.append(options["bottom_right_junction_char"])
        end_line = "".join(end_line)
        
        bits.insert(0, first_line)
        bits.append(end_line)
        
        return "\n".join(bits)
    
    def _stringify_row(self, row, options, hrule):
        for (index, field, value, width) in zip(
                range(0, len(row)), self._field_names, row, self._widths
        ):
            # Enforce max widths
            lines = value.split("\n")
            new_lines = []
            for line in lines:
                if str_block_width(line) > width:
                    line = self.wrap_func(line, width)
                new_lines.append(line)
            lines = new_lines
            value = "\n".join(lines)
            row[index] = value
        
        row_height = 0
        for one in row:
            height = get_size(one)[1]
            if height > row_height:
                row_height = height
        
        bits = []
        lpad, rpad = self._get_padding_widths(options)
        for i in range(0, row_height):
            bits.append([])
            if options["border"]:
                if options["vrules"] in (ALL, FRAME):
                    bits[i].append(self.vertical_char)
                else:
                    bits[i].append(" ")
        
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
            i = 0
            for line in lines:
                if options["fields"] and field not in options["fields"]:
                    continue
                bits[i].append(
                    " " * lpad
                    + self._justify(line, width, self._align[field])
                    + " " * rpad
                )
                if options["border"]:
                    if options["vrules"] == ALL:
                        bits[i].append(self.vertical_char)
                    else:
                        bits[i].append(" ")
                i += 1
        # If vrules is FRAME, then we just appended a space at the end
        # of the last field, when we really want a vertical character
        for i in range(0, row_height):
            if options["border"] and options["vrules"] == FRAME:
                bits[i].pop()
                bits[i].append(options["vertical_char"])
        
        if options["border"] and options["hrules"] == ALL:
            bits[row_height - 1].append("\n")
            bits[row_height - 1].append(hrule)
        
        for i in range(0, row_height):
            bits[i] = "".join(bits[i])
        
        return "\n".join(bits)
    
    # def get_image(self, **kwargs):
    #     return table2image(str(self), **kwargs)
    
    def __str__(self):
        return self.get_string()
    
    def __add__(self, other):
        return hstack(self, other)


class MultiTable(object):
    """多表格类"""
    
    def __init__(self, tables):
        self._tables = tables
        self._table_width = 0
    
    def add_table(self, table):
        """增加表格"""
        assert isinstance(table, AwesomeTable)
        self._tables.append(table)
    
    @property
    def table_width(self):
        """表格宽度"""
        return self._table_width
    
    @table_width.setter
    def table_width(self, val):
        self._table_width = val
        for table in self._tables:
            table.table_width = val
    
    def get_string(self):
        """多表字符串"""
        if self._table_width == 0:
            self.table_width = max([t.table_width for t in self._tables])
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


def clear_symbols(table):
    """清除所有制表符
    
    :param table:
    :return:
    """
    out = ""
    for char in table:
        if char in ALL_SYMBOLS:
            out += " "
        else:
            out += char
    return out


def _align_cell(cell, align="color"):
    striped_cell = cell.strip()
    lpad = (len(cell) - len(striped_cell)) // 2
    rpad = len(cell) - len(striped_cell) - lpad
    if align == "color":
        new_cell = (lpad * " ") + striped_cell + (rpad * " ")
    elif align == "l":
        new_cell = " " + striped_cell + ((lpad + rpad - 1) * " ")
    elif align == "r":
        new_cell = ((lpad + rpad - 1) * " ") + striped_cell + " "
    else:
        raise KeyError
    return new_cell


def set_align(table, cno, align, rno=None):
    """设置表格对齐方式
    
    :param table: AwesomeTable
    :param cno: int 单元格号
    :param align: str 对齐方式
    :param rno: int 行号
    :return: str
    """
    lines = str(table).splitlines()
    if rno is None:
        out = []
        for line in lines:
            if "═" in line:
                out.append(line)
            else:
                cells = re.split(V_LINE_PATTERN, line)[1:-1]
                try:
                    cell = cells[cno]
                except IndexError:
                    continue
                new_cell = _align_cell(cell, align)
                line = line.replace(cell, new_cell)
                out.append(line)
        return "\n".join(out)
    
    line = lines[2 * rno + 1]
    cells = re.split(V_LINE_PATTERN, line)[1:-1]
    cell = cells[cno]
    new_cell = _align_cell(cell, align)
    lines[2 * rno + 1] = line.replace(cell, new_cell)
    return "\n".join(lines)


def merge_row(table, rno):
    """合并同一行的cells
    
    :param table: AwesomeTable | str
    :param rno: int
    :return: str
    """
    lines = str(table).splitlines()
    line = lines[2 * rno + 1]
    new_line = "║" + line.replace("║", " ")[1:-1] + "║"
    lines[2 * rno + 1] = new_line
    return "\n".join(lines)


def remove_hor_line(table, start=2, end=-1, keep_blank=True):
    """移除中间的横线
    
    :param table: AwesomeTable | str
    :param start: int 起始行号
    :param end: int 结束行号
    :param keep_blank: bool 保持空行
    :return: str
    """
    lines = str(table).splitlines()
    if keep_blank:
        lines[start:end:2] = [
            "║" + (len(line) - 2) * " " + "║" for line in lines[start:end:2]
        ]
    else:
        del lines[start:end:2]
    return "\n".join(lines)


def add_width(table, num=1, align='m'):
    """增加表格宽度
    
    :param table: AwesomeTable | str
    :param num: int 字符数
    :return: str
    """
    lines = str(table).splitlines()
    newlines = []
    for line in lines:
        try:
            char = line[-2]
            if char == "═":
                newline = line[0] + line[1:-1] + line[-2] * num + line[-1]
            elif "║" in line:
                cells = line.rsplit("║", 2)
                if align == 'm':
                    newline = (
                            cells[0]
                            + "║"
                            + " " * (num // 2)
                            + cells[1]
                            + " " * (num - num // 2)
                            + "║"
                    )
                elif align == 'l':
                    newline = (
                            cells[0]
                            + "║"
                            + cells[1]
                            + " " * num
                            + "║"
                    )
                elif align == 'r':
                    newline = (
                            cells[0]
                            + "║"
                            + " " * num
                            + cells[1]
                            + "║"
                    )
                else:
                    raise ValueError('align in l m r')
            else:
                newline = line
        except IndexError:
            newline = line
        newlines.append(newline)
    return "\n".join(newlines)


def add_newline(table, num=1, align="t"):
    """纵向拉伸,直接加到末尾
    
    :param table: AwesomeTable | str
    :param num: int 行数
    :param align: str 对齐方式
    :return: str
    """
    idx = -1
    scale_lines = str(table).splitlines()
    if align == "t":
        idx = -1
    elif align == "b":
        idx = 0
    end_line = scale_lines[idx]
    insect_line = []
    for char in end_line:
        if char == "═":
            insect_line.append(" ")
        else:
            insect_line.append("║")
    insect_line = "".join(insect_line)
    if align == "t":
        for _ in range(num):
            scale_lines.insert(idx, insect_line)
    else:
        for _ in range(num):
            scale_lines.insert(1, insect_line)
    return "\n".join(scale_lines)


def _hstack(self, other, merged=True, space=0, align="t"):
    """表格字符横向拼接
    
    :param self: AwesomeTable | str 左侧
    :param other: AwesomeTable | str 右侧
    :param merged: bool 是否连接
    :param space: int 若不连接使用的空格数
    :param align: str 扩展行的对齐方式 't'顶端对齐 'b'底端对齐
    :return: str
    """
    sos = str(self)  # str of self
    soo = str(other)  # str of other
    hos = len(sos.splitlines())
    hoo = len(soo.splitlines())
    if hos > hoo:
        soo = add_newline(soo, hos - hoo, align)
    elif hos < hoo:
        sos = add_newline(sos, hoo - hos, align)
    else:
        pass
    self_lines = sos.splitlines()
    other_lines = soo.splitlines()
    new_lines = []
    for left, right in zip(self_lines, other_lines):
        if merged:
            eol = left[-1]
            bor = right[0]
            if eol == bor == "║":
                ret = "║"
            elif eol == "╗" and bor == "╔":
                ret = "╦"
            elif eol == "╣" and bor == "║":
                ret = "╣"
            elif eol == "╣" and bor == "╠":
                ret = "╬"
            elif eol == "║" and bor == "╠":
                ret = "╠"
            elif eol == "╝" and bor == "╚":
                ret = "╩"
            else:
                print(other)
                raise Exception("Unmatch symbol %s and %s" % (eol, bor))
            new_lines.append(left[:-1] + ret + right[1:])
        else:
            new_lines.append(left + " " * space + right)
    return "\n".join(new_lines)


def _vstack(self, other, merged=True, align='m'):
    """表格字符纵向拼接
    
    :param self: AwesomeTable | str 左侧
    :param other: AwesomeTable | str 左侧
    :param merged: bool 是否合并
    :return: str
    """
    sos = str(self)  # str of self
    soo = str(other)  # str of other
    hos = len(sos.splitlines()[0])
    hoo = len(soo.splitlines()[0])
    if hos > hoo:
        soo = add_width(soo, hos - hoo, align)
    elif hos < hoo:
        sos = add_width(sos, hoo - hos, align)
    else:
        pass
    if sos.splitlines()[-1][-1] != "╝" or soo[0] != "╔":
        return sos + "\n" + soo
    if not merged:
        return sos + "\n" + soo  # {' '*len(sos.splitlines()[0])}
    
    end_of_self = sos.splitlines()[-1]
    begin_of_other = soo.splitlines()[0]
    ret = []
    for end, beg in zip(end_of_self, begin_of_other):
        if end == beg == "═":
            ret.append(end)
        elif end == "╚" and beg == "╔":
            ret.append("╠")
        elif end == "╝" and beg == "╗":
            ret.append("╣")
        elif end == "╩" and beg == "╦":
            ret.append("╬")
        elif end == "╩" and beg == "═":
            ret.append("╩")
        elif end == "═" and beg == "╦":
            ret.append("╦")
        elif end == "═" and beg == "╗":
            ret.append("╗")
        else:
            raise Exception("Unmatch symbol %s and %s" % (end, beg))
    midline = "".join(ret)
    new_lines = sos.splitlines()[:-1] + [midline] + soo.splitlines()[1:]
    return "\n".join(new_lines)


def hstack(tables, other=None, merged=True, align='t'):
    """横向连接多个表格
    
    :param tables: list[AwesomeTable] | AwesomeTable
    :param other: None | AwesomeTable
    :return: str
    """
    if isinstance(tables, list) and other is None:
        return reduce(partial(_hstack, merged=merged, align=align), tables)
    return _hstack(tables, other, merged, align)


def vstack(tables, other=None, merged=True, align='m'):
    """纵向连接多个表格
    
    :param tables: list[AwesomeTable] | AwesomeTable
    :param other: None | AwesomeTable
    :return: str
    """
    if isinstance(tables, list) and other is None:
        return reduce(partial(_vstack, merged=merged, align=align), tables)
    return _vstack(tables, other, merged, align)


def stack(tables):
    """合并多个表格
    
    :param tables: list[list[AwesomeTable|str]]
    :return: str
    """
    return vstack([hstack(table) for table in tables])


def wrap(line, width):
    """考虑了中文宽度和字母宽度不一样
    
    :param line: str
    :param width: int
    :return: str
    """
    lines = []
    new_line = ""
    for char in line:
        if not char.isprintable():  # 忽略不可见字符
            continue
        new_line += char
        if str_block_width(new_line) == width:
            lines.append(new_line)
            new_line = ""
        elif str_block_width(new_line) > width:
            lines.append(new_line[:-1])
            new_line = new_line[-1]
        else:
            continue
    if new_line:
        lines.append(new_line)
    return "\n".join(lines)


def count_padding(text):
    """计算字符串的前缀空格数和后缀空格数
    
    :param text: str
    :return: tuple[int,int]
    """
    lpad, rpad = 0, 0
    for i in text:
        if i == " ":
            lpad += 1
        else:
            break
    for i in text[::-1]:
        if i == " ":
            rpad += 1
        else:
            break
    return lpad, rpad


def replace_chinese_to_dunder(lines, lno):
    """ 将中文字符替换为双下划线
    
    :param lines: list[str] 字符串列表
    :param lno: int 行号
    :return: str
    """
    out = []
    for char in lines[lno]:
        if str_block_width(char) == 2:
            out.append("__")
        else:
            out.append(char)
    return "".join(out)
