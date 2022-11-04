"""
财务报表假数据供应商
"""
import functools
import random
import re

from faker.providers import BaseProvider

from awesometable.awesometable import AwesomeTable, V_LINE_PATTERN, vstack
from awesometable.converter import from_list

# from awesometable.fontwrap import font_wrap


class Provider(BaseProvider):
    """表格相关的假数据供应商"""

    def word(self):
        raise NotImplementedError

    def words(self, nb=3, ext_word_list=None, unique=False):
        raise NotImplementedError

    def sentence(self, num):
        raise NotImplementedError

    def price(self, digits=None, fix_len=True, unsigned=False, empty_ratio=0):
        num = self.random_number(digits, fix_len)
        if not unsigned:
            if random.random() < 0.5:
                num = -num
        if random.random() < empty_ratio:
            return "-"
        return f"{num:,}"

    def index(self):
        return self.word().capitalize()

    def indexes(self, num, unique=False):
        return self.words(num, unique=unique)

    def columns(self, num=None):
        return self.words(num)

    def title(self, low=5, high=8):
        num = random.randint(low, high)
        return self.sentence(num)

    def subtitle(self, max_len=1):
        assert max_len >= 1
        num = random.randint(1, max_len)
        return " ".join(self.words(num)).upper()

    def subtitle_lines(self, rows, min=2, max=5):
        i = 0
        subtitle_rows = []
        while i < rows - 1:
            subtitle_rows.append(i)
            n = random.randint(min, max)
            i += n
        return subtitle_rows

    def paragraph(self, nb=3):
        return " ".join([self.sentence() for _ in range(nb)])

    def style(self):
        return self.random_element(["striped", "other", "simple"])

    def _gen_header(self, c, w, h=tuple(range(5))):
        """枚举复杂表头格式
        不要试图去优化这段代码,<arry_lee@qq.com>
        """
        if len(c) == 4:
            t1 = [{c[0]: w[0]}, {h[0]: {c[1]: w[1], c[2]: w[2], c[3]: w[3]}}]
            return t1
        elif len(c) == 5:
            t1 = [
                {c[0]: w[0]},
                {h[0]: {c[1]: w[1], c[2]: w[2]}},
                {h[1]: {c[3]: w[3], c[4]: w[4]}},
            ]
            t2 = [
                {c[0]: w[0]},
                {h[0]: {c[1]: w[1], c[2]: w[2], c[3]: w[3], c[4]: w[4]}},
            ]
            t3 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[0]: {c[1]: w[1], c[2]: w[2]},
                        h[1]: {c[3]: w[3], c[4]: w[4]},
                    }
                },
            ]
            t = random.choice([t1, t2, t3])
        elif len(c) == 6:
            t1 = [
                {c[0]: w[0]},
                {h[0]: {c[1]: w[1], c[2]: w[2]}},
                {c[3]: w[3]},
                {h[1]: {c[4]: w[4], c[5]: w[5]}},
            ]
            t2 = [
                {c[0]: w[0]},
                {h[0]: {c[1]: w[1], c[2]: w[2], c[3]: w[3], c[4]: w[4], c[5]: w[5]}},
            ]
            t3 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[1]: {c[1]: w[1], c[2]: w[2]},
                        h[2]: {c[3]: w[3], c[4]: w[4]},
                        c[5]: w[5],
                    }
                },
            ]
            t = random.choice([t1, t2, t3])
        elif len(c) == 7:
            t1 = [
                {c[0]: w[0]},
                {h[0]: {h[2]: {c[1]: w[1], c[2]: w[2]}, c[3]: w[3]}},
                {h[1]: {h[2]: {c[4]: w[4], c[5]: w[5]}, c[6]: w[6]}},
            ]
            t2 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[2]: {c[1]: w[1], c[2]: w[2]},
                        c[3]: w[3],
                        h[3]: {c[4]: w[4], c[5]: w[5]},
                        c[6]: w[6],
                    }
                },
            ]
            t = random.choice([t1, t2])
        elif len(c) == 8:
            t1 = [
                {c[0]: w[0]},
                {h[0]: {h[2]: {c[1]: w[1], c[2]: w[2]}, c[3]: w[3]}},
                {h[1]: {h[2]: {c[4]: w[4], c[5]: w[5]}, c[6]: w[6], c[7]: w[7]}},
            ]
            t2 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[1]: {c[1]: w[1], c[2]: w[2], c[3]: w[3]},
                        h[2]: {c[4]: w[4], c[5]: w[5]},
                        h[3]: {c[6]: w[6], c[7]: w[7]},
                    }
                },
            ]
            t = random.choice([t1, t2])
        elif len(c) == 9:
            t1 = [
                {c[0]: w[0]},
                {h[0]: {h[2]: {c[1]: w[1], c[2]: w[2]}, c[3]: w[3], c[4]: w[4]}},
                {h[1]: {h[2]: {c[5]: w[5], c[6]: w[6]}, c[7]: w[7], c[8]: w[8]}},
            ]
            t2 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[2]: {c[1]: w[1], c[2]: w[2]},
                        h[3]: {c[3]: w[3], c[4]: w[4]},
                    }
                },
                {
                    h[1]: {
                        h[2]: {c[5]: w[5], c[6]: w[6]},
                        h[3]: {c[7]: w[7], c[8]: w[8]},
                    }
                },
            ]
            t3 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[1]: {c[1]: w[1], c[2]: w[2]},
                        h[2]: {c[3]: w[3], c[4]: w[4]},
                        h[3]: {c[5]: w[5], c[6]: w[6]},
                        h[4]: {c[7]: w[7], c[8]: w[8]},
                    }
                },
            ]
            t = random.choice([t1, t2, t3])
        elif len(c) == 10:
            t1 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[2]: {c[1]: w[1], c[2]: w[2]},
                        h[3]: {c[3]: w[3], c[4]: w[4]},
                    }
                },
                {
                    h[1]: {
                        h[2]: {c[5]: w[5], c[6]: w[6]},
                        h[3]: {c[7]: w[7], c[8]: w[8], c[9]: w[9]},
                    }
                },
            ]
            t2 = [
                {c[0]: w[0]},
                {h[0]: {h[2]: {c[1]: w[1], c[2]: w[2]}, c[3]: w[3], c[4]: w[4]}},
                {
                    h[1]: {
                        h[2]: {c[5]: w[5], c[6]: w[6]},
                        c[7]: w[7],
                        c[8]: w[8],
                        c[9]: w[9],
                    }
                },
            ]
            t3 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[1]: {c[1]: w[1], c[2]: w[2]},
                        h[2]: {c[3]: w[3], c[4]: w[4]},
                        h[3]: {c[5]: w[5], c[6]: w[6]},
                        h[4]: {c[7]: w[7], c[8]: w[8], c[9]: w[9]},
                    }
                },
            ]
            t = random.choice([t1, t2, t3])
        elif len(c) == 11:
            t1 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[2]: {c[1]: w[1], c[2]: w[2]},
                        h[3]: {c[3]: w[3], c[4]: w[4]},
                        c[5]: w[5],
                    }
                },
                {
                    h[1]: {
                        h[2]: {c[6]: w[6], c[7]: w[7]},
                        h[3]: {c[8]: w[8], c[9]: w[9]},
                        c[10]: w[10],
                    }
                },
            ]
            t2 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[1]: {c[1]: w[1], c[2]: w[2]},
                        h[2]: {c[3]: w[3], c[4]: w[4]},
                        h[3]: {c[5]: w[5], c[6]: w[6], c[7]: w[7]},
                        h[4]: {c[8]: w[8], c[9]: w[9], c[10]: w[10]},
                    }
                },
            ]
            t = random.choice([t1, t2])
        elif len(c) == 12:
            t1 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[2]: {c[1]: w[1], c[2]: w[2]},
                        h[3]: {c[3]: w[3], c[4]: w[4]},
                        c[5]: w[5],
                    }
                },
                {
                    h[1]: {
                        h[2]: {c[6]: w[6], c[7]: w[7]},
                        h[3]: {c[8]: w[8], c[9]: w[9]},
                        c[10]: w[10],
                        c[11]: w[11],
                    }
                },
            ]
            t2 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[1]: {c[1]: w[1], c[2]: w[2]},
                        h[2]: {c[3]: w[3], c[4]: w[4], c[5]: w[5]},
                        h[3]: {c[6]: w[6], c[7]: w[7]},
                        h[4]: {c[8]: w[8], c[9]: w[9]},
                        c[10]: w[10],
                        c[11]: w[11],
                    }
                },
            ]
            t = random.choice([t1, t2])
        elif len(c) == 13:
            t1 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[2]: {c[1]: w[1], c[2]: w[2]},
                        h[3]: {c[3]: w[3], c[4]: w[4]},
                        c[5]: w[5],
                        c[6]: w[6],
                    }
                },
                {
                    h[1]: {
                        h[2]: {c[7]: w[7], c[8]: w[8]},
                        h[3]: {c[9]: w[9], c[10]: w[10]},
                        c[11]: w[11],
                        c[12]: w[12],
                    }
                },
            ]
            t2 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[1]: {c[1]: w[1], c[2]: w[2]},
                        h[2]: {c[3]: w[3], c[4]: w[4]},
                        c[5]: w[5],
                        c[6]: w[6],
                        h[3]: {c[7]: w[7], c[8]: w[8]},
                        h[4]: {c[9]: w[9], c[10]: w[10]},
                        c[11]: w[11],
                        c[12]: w[12],
                    }
                },
            ]
            t = random.choice([t1, t2])
        elif len(c) == 14:
            t1 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[2]: {c[1]: w[1], c[2]: w[2]},
                        h[3]: {c[3]: w[3], c[4]: w[4]},
                        c[5]: w[5],
                        c[6]: w[6],
                    }
                },
                {
                    h[1]: {
                        h[2]: {c[7]: w[7], c[8]: w[8]},
                        h[3]: {c[9]: w[9], c[10]: w[10]},
                        c[11]: w[11],
                        c[12]: w[12],
                        c[13]: w[13],
                    }
                },
            ]
            t2 = [
                {c[0]: w[0]},
                {
                    h[0]: {
                        h[1]: {c[1]: w[1], c[2]: w[2]},
                        h[2]: {c[3]: w[3], c[4]: w[4]},
                        c[5]: w[5],
                        c[6]: w[6],
                        h[3]: {c[7]: w[7], c[8]: w[8]},
                        h[4]: {c[9]: w[9], c[10]: w[10]},
                        c[11]: w[11],
                        c[12]: w[12],
                        c[13]: w[13],
                    }
                },
            ]
            t = random.choice([t1, t2])
        else:
            raise KeyError()
        return t

    def build_complex_header(self, t, cc=None):
        lines = str(t).splitlines()
        # 移除表原来的表头
        for i in range(1, len(lines)):
            if lines[i][0] == "╠":
                break
        nt = lines[0] + "\n" + "\n".join(lines[i + 1 :])
        w = [len(c) + 2 for c in re.split(V_LINE_PATTERN, lines[0])[1:-1]]
        assert len(w) == len(cc)
        cc = [x.title() for x in cc]
        header = tuple(x.title() for x in self.words(len(cc)))
        _header = from_list(self._gen_header(cc, w, header), False)
        return vstack(_header, nt)

    def table(
        self,
        nr=3,
        nc=6,
        width=None,
        indent=False,
        complex_header=False,
        double_column=False,
        large_gap=False,
    ):
        indexes = self.indexes(nr)
        columns = self.columns(nc)

        a = AwesomeTable()
        a.add_row(columns)

        for lno, i in enumerate(indexes):
            row = [self.price() for _ in columns]

            if indent:
                if lno % 3 == 0:
                    row[0] = i.upper()
                    row[1:] = [""] * (nc - 1)
                else:
                    row[0] = i.capitalize()
            else:
                row[0] = i.capitalize()
            if double_column:
                if indent:
                    if 2 * lno % 3 == 0:
                        row[nc // 2] = self.index().upper()
                    else:
                        row[nc // 2] = self.index().capitalize()
                else:
                    row[nc // 2] = self.index().capitalize()
            a.add_row(row)
        a.align = "r"
        a._align["Field 1"] = "l"
        a.max_width = 20

        if width:
            a.table_width = width

        if large_gap:
            a.widths = []
            tw = a._table_width - nc - 1
            nw = tw // 10  # 按照10等份，后面的各取1份，剩下的给前面
            a.widths = [nw] * (nc - 1)
            a.widths.insert(0, tw - nw * (nc - 1))
        if complex_header:
            s = a.get_string()
            a = self.build_complex_header(s, columns)
        return a
