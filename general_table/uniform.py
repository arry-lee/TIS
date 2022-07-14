import random

import prettytable

from awesometable.awesometable import (AwesomeTable, _hstack, _vstack, hstack,
                                       vstack, wrap)
from awesometable.converter import from_dict
from data_generator.fakekeys import key_value_generator


class UniForm(object):
    """根据配置的参数随机生成通用表格"""

    def __init__(self, config):
        self.config = config
        self.data = config["form_type"]
        self.rows = []
        self.filters = config["filters"]
        self.table_width = self.filters["max_table_width"]
        self.min_width_of_cell = self.filters.get("min_width_of_cell", 4)
        label_dir = config["base"]["label_dir"]
        print(label_dir)
        (
            self.keys_dict,
            self.values_dict,
            self.texts,
            self.keys,
            self.values,
        ) = key_value_generator(label_dir)

        self.empty_cell_ratio = self.filters.get("empty_cell_ratio", 0.05)
        self.long_text_ratio = self.filters.get("long_text_ratio", 0.1)

    def rand_text(self, l, place_holder="_"):
        if place_holder == "key":
            return random.choice(self.keys_dict.get(l, self.keys))
        elif place_holder == "value":
            if random.random() < self.empty_cell_ratio:  # 单元格空值的
                return " " * l
            elif random.random() < self.long_text_ratio:  # 长文本概率
                return random.choice(wrap(self.texts, 10))
            else:
                return random.choice(self.values_dict.get(l, self.values))

        else:
            return random.choice(self.texts)

    def rand_dict(self, n, cols, rows):
        if n > 1:
            d = {}
            for i in range(cols):
                d[self.rand_text(4, place_holder="key")] = self.rand_dict(
                    n - 1, cols, rows
                )
            return d
        else:
            d = {}
            for i in range(cols):
                d[self.rand_text(4, place_holder="key")] = [
                    self.rand_text(4, place_holder="value") for _ in range(rows)
                ]
            return d

    def mxn(self, m, n, w, t=0):
        """表格的基本元生成"""
        rows = [
            [self.rand_text(4, place_holder="value") for _ in range(m)]
            for x in range(n)
        ]
        tab = AwesomeTable()
        tab.table_width = w
        tab.add_rows(rows)
        if t:
            tab.title_pos = "_ltb"[t]
            tab.title = self.rand_text(4, place_holder="key")
        tab.min_width = self.min_width_of_cell
        return tab

    def filter(self, table):
        if self.filters.get("disable", True):
            return True

        lines = table.splitlines()
        width = len(lines[0])
        rows = len(lines)
        # if self.filters.get('max_table_width', None):
        #     if width > self.filters.get('max_table_width'):
        #         return False
        #     if width < self.filters.get('min_table_width'):
        #         return False
        # if self.filters.get('max_num_of_rows', None):
        #     if rows > self.filters.get('max_num_of_rows'):
        #         return False
        if rows < self.filters.get("min_num_of_rows"):
            return False
        return True

    def create(self, iteration=1):
        for i in range(iteration):
            rows = []
            for k, v in self.data.items():
                func = self.__getattribute__(k)
                if random.random() < v.get("probability"):  # 出现概率
                    max_ = v.get("max_num", 1)
                    min_ = v.get("min_num", 1)
                    times = random.randint(min_, max_)
                    for i in range(times):
                        rows.append(func(**v))
                else:
                    pass

            random.shuffle(rows)

            if random.random() < self.filters["vstack_split_ratio"]:
                mid = len(rows) // 2
                top = vstack(rows[:mid])
                bottom = vstack(rows[mid:])

                top, bottom = _vstack(top, bottom, False).split("\n\n")

                sepr = "".join(
                    [
                        self.rand_text(random.randint(4, 10),
                                       place_holder="key")
                        for r in range(random.randint(1, 3))
                    ]
                )

                ret = "\n".join([top, sepr, bottom])
            else:
                if len(rows) > 1:
                    ret = vstack(rows)
                else:
                    ret = rows[0]

            if self.filter(ret):
                yield ret
            else:
                continue

    def run(self, batch):
        """无尽表格生成器"""
        queue = list()
        for i in range(batch):
            rows = []
            for k, v in self.data.items():
                func = self.__getattribute__(k)
                if random.random() < v.get("probability"):  # 出现概率
                    max_ = v.get("max_num", 1)
                    min_ = v.get("min_num", 1)
                    times = random.randint(min_, max_)
                    for i in range(times):
                        t = func(**v)
                        # print(t)
                        rows.append(t)
                else:
                    pass
            random.shuffle(rows)
            queue.extend(rows)
        return queue

    def single_line(self, **kwargs):
        t = AwesomeTable()
        t.add_row([self.rand_text(26)])
        t.table_width = self.table_width
        return t

    def multiline_text(self, **kwargs):
        if not kwargs:
            kwargs = self.data.get("multiline_text")
        max_num_of_rows = kwargs["max_num_of_rows"]
        min_num_of_rows = kwargs["min_num_of_rows"]
        num = random.randint(min_num_of_rows, max_num_of_rows)
        multi_text = []
        for i in range(num):
            multi_text.append(
                str(i + 1) + "." + self.rand_text(random.randint(10, 20)))
        t = AwesomeTable()
        t.add_rows([[x] for x in multi_text])
        t.table_width = self.table_width
        t.vrules = prettytable.FRAME
        t.hrules = prettytable.FRAME

        t.align = "l"
        has_title = random.random() < kwargs["has_title_raito"]
        if not has_title:
            return t
        else:
            tt = AwesomeTable()
            title = self.rand_text(random.choice((4, 6, 8)), place_holder="key")
            tt.add_row([title])
        t.table_width = self.table_width - tt.table_width + 1
        return _hstack(tt, t)

    def single_key_value(self, **kwargs):
        k = self.rand_text(6, place_holder="key")
        v = self.rand_text(random.randint(8, 16), place_holder="value")
        t = AwesomeTable()
        t.add_row([k])
        t.min_width = self.min_width_of_cell
        vt = AwesomeTable()
        vt.add_row([v])
        vt.table_width = self.table_width - t.table_width + 1
        vt.min_width = self.min_width_of_cell
        return _hstack(t, vt)

    def multiple_key_value_pairs(self, **kwargs):
        if not kwargs:
            kwargs = self.data.get("multiple_key_value_pairs")
        min_num_of_pairs = kwargs["min_num_of_pairs"]
        max_num_of_pairs = kwargs["max_num_of_pairs"]
        num = random.randint(min_num_of_pairs, max_num_of_pairs)
        pairs = []
        for i in range(num):
            pairs.append(self.rand_text(6, place_holder="key"))
            pairs.append(
                self.rand_text(random.randint(8, 16), place_holder="value"))
        t = AwesomeTable()
        t.add_row(pairs)
        t.min_width = self.min_width_of_cell
        # t.table_width = self.table_width
        return t

    def single_key_multiple_values(self, **kwargs):
        if not kwargs:
            kwargs = self.data.get("single_key_multiple_values")
        max_options = kwargs["max_options"]
        min_options = kwargs["min_options"]
        num = random.randint(min_options, max_options)
        choices = []

        for i in range(num):
            choices.append(
                "[x]" + self.rand_text(random.randint(4, 8),
                                       place_holder="value")
            )

        k = self.rand_text(6, place_holder="key")
        kt = AwesomeTable()

        kt.add_row([k])
        kt.min_width = self.min_width_of_cell
        vt = AwesomeTable()
        vt.add_row(choices)
        vt.vrules = prettytable.FRAME
        vt.table_width = self.table_width - kt.table_width + 1
        return _hstack(kt, vt)

    def multiple_rows_multiple_columns(self, **kwargs):
        if not kwargs:
            kwargs = self.data.get("multiple_rows_multiple_columns")
        min_num_of_rows = kwargs["min_num_of_rows"]
        max_num_of_rows = kwargs["max_num_of_rows"]
        min_num_of_cols = kwargs["min_num_of_cols"]
        max_num_of_cols = kwargs["max_num_of_cols"]
        rows = random.randint(min_num_of_rows, max_num_of_rows)
        cols = random.randint(min_num_of_cols, max_num_of_cols)

        table = [
            [
                self.rand_text(random.randint(2, 6), place_holder="value")
                for _ in range(cols)
            ]
            for _ in range(rows)
        ]

        head_top = random.random() < kwargs["header_top_ratio"]
        head_left = random.random() < kwargs["header_left_ratio"]

        if head_top:
            table[0] = [
                self.rand_text(random.randint(2, 6), place_holder="key")
                for _ in range(cols)
            ]
        if head_left:
            for i in range(rows):
                table[i][0] = self.rand_text(random.randint(2, 6),
                                             place_holder="key")
        tt = AwesomeTable()
        tt.add_rows(table)

        if random.random() < kwargs["vrules_all_ratio"]:
            tt.vrules = prettytable.ALL
        else:
            tt.vrules = prettytable.FRAME
        if random.random() < kwargs["hrules_all_ratio"]:
            tt.hrules = prettytable.ALL
        else:
            tt.hrules = prettytable.FRAME

        if self.table_width > 0:
            tt.table_width = self.table_width
        tt.min_width = self.min_width_of_cell
        return str(tt)

    def complex(self, **kwargs):
        """复杂表头横向对齐问题需要解决"""
        if not kwargs:
            kwargs = self.data.get("complex")
        min_depth_of_header = kwargs["min_depth_of_header"]
        max_depth_of_header = kwargs["max_depth_of_header"]
        depth = random.randint(min_depth_of_header, max_depth_of_header)

        min_num_of_cols = kwargs["min_num_of_cols"]
        max_num_of_cols = kwargs["max_num_of_cols"]
        cols = random.randint(min_num_of_cols, max_num_of_cols)

        min_num_of_rows = kwargs["min_num_of_rows"]
        max_num_of_rows = kwargs["max_num_of_rows"]
        rows = random.randint(min_num_of_rows, max_num_of_rows)

        d = self.rand_dict(depth, cols, rows)
        t2b = random.random() > kwargs["left_to_right_ratio"]  # 从上到下的概率

        if t2b:
            if random.random() < kwargs["fixed_width_ratio"]:
                max_width = max(self.table_width // (cols ** depth), 12)
                return from_dict(d, t2b, max_width)
            else:
                return from_dict(d, t2b)
        else:
            if random.random() < kwargs["fixed_width_ratio"]:
                max_width = max(self.table_width // (depth + rows),
                                12)  # 保证同宽度的补丁
                return from_dict(d, t2b, max_width)
            else:
                return from_dict(d, t2b)

    def cross_rows_cross_cols(self, **kwargs):
        """跨行跨列的情况"""
        if not kwargs:
            kwargs = self.data.get("cross_rows_cross_cols")
        nob = random.randint(2, kwargs.get("max_num_of_blocks", 2))
        blocks = []
        blocks_width = self.table_width // nob  # 平均宽度

        for i in range(nob):
            noc = random.randint(2, kwargs.get("max_num_of_cols", 2))
            nor = random.randint(2, kwargs.get("max_num_of_rows", 2))
            t = random.randint(0, 3)
            b = self.mxn(noc, nor, blocks_width, t)
            blocks.append(b)
        return hstack(blocks)

# if __name__ == '__main__':
# import sys
# config = sys.argv[1]
# batch = int(sys.argv[2])
# f = UniFacory(config=config,batch=batch)
# f.start()
# f2 = UniFactory(config='config/config.yaml', batch=1)
# f2.start()
