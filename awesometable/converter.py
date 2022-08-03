# 进行各种数据结构和表示方法向AwesomeTable转换
import prettytable

from .awesometable import AwesomeTable, hstack, vstack


def dict2table(
    d, title=None, title_pos="t", n=3, has_line=True, direct="h", table_width=None
):
    """将字典转为table"""
    table = AwesomeTable()
    if table_width:
        table.table_width = table_width

    if direct == "h":
        row = []
        for k, v in d.items():
            row.append(k)
            row.append(v)
            if len(row) == n * 2:
                table.add_row(row)
                row = []
    else:
        table.add_row([k for k in d.keys()])
        table.add_row([str(k) for k in d.values()])
        table.header = True
    if title:
        table.title = title
        table.title_pos = title_pos

    if has_line:
        table.vrules = prettytable.ALL
        table.hrules = prettytable.ALL
    else:
        table.vrules = prettytable.FRAME
        table.hrules = prettytable.ALL
    return table


def from_dataframe(df, field_names=None, **kwargs):
    if not field_names:
        field_names = list(df.columns)
    table = prettytable.PrettyTable(kwargs)
    table.vrules = prettytable.ALL
    table.hrules = prettytable.ALL

    table.header = False
    table.set_style(15)
    table.add_row(field_names)
    for row in df.values:
        table.add_row(row.tolist())
    table.align = "l"
    return table.get_string()


def from_str(s, w=None):
    t = AwesomeTable(align="l")
    t.add_row([str(s)])
    if w:
        t.table_width = w
    t.min_width = 4
    return t


def from_json(jsobj):
    """递归的将json转换为table"""
    cols = []
    for key, value in jsobj.items():
        a = AwesomeTable()
        a.add_row([key])
        if isinstance(value, dict):
            tv = from_json(value)
        elif isinstance(value, list):
            tv = AwesomeTable()
            for v in value:
                tv.add_row([v])
        elif isinstance(value, AwesomeTable):
            tv = value
        else:
            tv = AwesomeTable()
            tv.add_row([str(value)])
        col = vstack(a, tv)
        cols.append(col)
    return hstack(cols)


def from_json_v(jsobj):
    rows = []
    for key, value in jsobj.items():
        title = from_str(key)

        if isinstance(value, dict):
            tv = from_json(value)

        elif isinstance(value, list):
            if isinstance(value[0], dict):
                tv = AwesomeTable()
                tv.add_row(list(value[0].keys()))
                for d in value:
                    tv.add_row(list(d.values()))
            else:
                tv = AwesomeTable()
                tv.add_row(value)

        elif isinstance(value, AwesomeTable):
            tv = value

        else:
            tv = AwesomeTable()
            tv.add_row([str(value)])
        row = hstack(title, tv)
        rows.append(row)
    return vstack(rows)


def from_list(ls, t2b=True, w=None):
    if t2b:
        rows = []
        for value in ls:
            if isinstance(value, dict):
                tv = from_dict(value, not t2b, w)
            elif isinstance(value, list):
                tv = from_list(value, not t2b, w)
            elif isinstance(value, AwesomeTable):
                tv = value
            else:
                tv = from_str(value, w)
            rows.append(tv)
        return vstack(rows)
    else:
        cols = []
        for value in ls:
            if isinstance(value, dict):
                tv = from_dict(value, not t2b, w)
            elif isinstance(value, list):
                tv = from_list(value, not t2b, w)
            elif isinstance(value, AwesomeTable):
                tv = value
            else:
                tv = from_str(value, w)
            cols.append(tv)
        return hstack(cols)


def from_dict(d, t2b=True, w=None):
    if t2b is False:
        rows = []
        for key, value in d.items():
            title = from_str(key, w)
            if value is None:
                row = title
            elif isinstance(value, int):
                row = from_str(key, value)
            else:
                if isinstance(value, dict):
                    tv = from_dict(value, t2b, w)
                elif isinstance(value, list):
                    tv = from_list(value, t2b, w)
                elif isinstance(value, AwesomeTable):
                    tv = value
                else:
                    tv = from_str(value, w)
                row = hstack(title, tv)
            rows.append(row)
        return vstack(rows)
    else:
        cols = []
        for key, value in d.items():
            title = from_str(key, w)
            if value is None:
                col = title
            elif isinstance(value, int):
                col = from_str(key, value)
            else:
                if isinstance(value, dict):
                    tv = from_dict(value, t2b, w)
                elif isinstance(value, list):
                    tv = from_list(value, t2b, w)
                elif isinstance(value, AwesomeTable):
                    tv = value
                else:
                    tv = from_str(value, w)
                col = vstack(title, tv)
            cols.append(col)

        return hstack(cols)


def convert(x):
    if isinstance(x, list):
        return from_list(x)
    elif isinstance(x, dict):
        return from_dict(x)
    else:
        return from_str(x)


def pprint(x):
    print(convert(x))
