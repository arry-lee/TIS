"""随机参数通用表格生成"""

import random

import prettytable
import yaml

from awesometable.awesometable import (
    AwesomeTable,
    hstack,
    vstack,
    wrap,
)
from awesometable.converter import from_dict
from .fakekeys import key_value_generator


class UniForm:
    """根据配置的参数随机生成通用表格"""

    def __init__(self, config):
        if isinstance(config, dict):
            self.config = config
        elif isinstance(config, str):
            with open(config, "r", encoding="utf-8") as cfg:
                self.config = yaml.load(cfg, Loader=yaml.SafeLoader)
        else:
            raise ValueError

        self.data = self.config["form_type"]
        self.rows = []
        self.filters = self.config["filters"]
        self.table_width = int(self.filters["max_table_width"])
        self.min_width_of_cell = self.filters.get("min_width_of_cell", 4)
        label_dir = self.config["base"]["label_dir"]
        (
            self.keys_dict,
            self.values_dict,
            self.texts,
            self.keys,
            self.values,
        ) = key_value_generator(label_dir)

        self.empty_cell_ratio = self.filters.get("empty_cell_ratio", 0.05)
        self.long_text_ratio = self.filters.get("long_text_ratio", 0.1)

    def rand_text(self, length, place_holder="_"):
        """
        随机文本
        :param length: int 长度
        :param place_holder: str 占位符
        :return: str
        """
        if place_holder == "key":
            return random.choice(self.keys_dict.get(length, self.keys))
        if place_holder == "value":
            if random.random() < self.empty_cell_ratio:  # 单元格空值的
                return " " * length
            if random.random() < self.long_text_ratio:  # 长文本概率
                return random.choice(wrap(self.texts, 10))
            return random.choice(self.values_dict.get(length, self.values))
        return random.choice(self.texts)

    def rand_dict(self, depth, cols, rows):
        """
        随机字典
        :param depth: int 字典层数
        :param cols: int 列数
        :param rows: int 行数
        :return: dict
        """
        if depth > 1:
            dic = {}
            for _ in range(cols):
                dic[self.rand_text(4, place_holder="key")] = self.rand_dict(
                    depth - 1, cols, rows
                )
            return dic
        dic = {}
        for _ in range(cols):
            dic[self.rand_text(4, place_holder="key")] = [
                self.rand_text(4, place_holder="value") for _ in range(rows)
            ]
        return dic

    def rand_table(self, cols, rows, width, title_pos=0):
        """
        表格的基本元生成
        :param cols: int 列数
        :param rows: int 行数
        :param width: int 字符宽度
        :param title_pos: 标题相对位置 取 0 1 2 3
        :return: AwesomeTable
        """
        tab = AwesomeTable()
        tab.table_width = width
        tab.add_rows(
            [
                [self.rand_text(4, place_holder="value") for _ in range(cols)]
                for x in range(rows)
            ]
        )
        if title_pos:
            tab.title_pos = "_ltb"[title_pos]
            tab.title = self.rand_text(4, place_holder="key")
        tab.min_width = self.min_width_of_cell
        return tab

    def filter(self, table):
        """过滤器"""
        if self.filters.get("disable", True):
            return True

        lines = table.splitlines()
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
        """
        表格生成器
        :param iteration: 数量
        :return: yield AwesomeTable
        """
        for _ in range(iteration):
            rows = []
            for key, val in self.data.items():
                func = self.__getattribute__(key)
                if random.random() < val.get("probability"):  # 出现概率
                    max_ = val.get("max_num", 1)
                    min_ = val.get("min_num", 1)
                    times = random.randint(min_, max_)
                    for _ in range(times):
                        rows.append(func(**val))
                else:
                    pass

            random.shuffle(rows)

            if random.random() < self.filters["vstack_split_ratio"]:
                mid = len(rows) // 2
                top = vstack(rows[:mid])
                bottom = vstack(rows[mid:])

                top, bottom = vstack(top, bottom, False).split("\n\n")

                sepr = "".join(
                    [
                        self.rand_text(random.randint(4, 10), place_holder="key")
                        for _ in range(random.randint(1, 3))
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
        for _ in range(batch):
            rows = []
            for key, val in self.data.items():
                func = self.__getattribute__(key)
                if random.random() < val.get("probability"):  # 出现概率
                    max_ = val.get("max_num", 1)
                    min_ = val.get("min_num", 1)
                    times = random.randint(min_, max_)
                    for _ in range(times):
                        rows.append(func(**val))
                else:
                    pass
            random.shuffle(rows)
            queue.extend(rows)
        return queue

    def single_line(self, **kwargs):
        """
        单行文字模式
        :param kwargs: None 为了统一接口方便映射
        :return: AwesomeTable
        """
        tab = AwesomeTable()
        tab.add_row([self.rand_text(26)])
        tab.table_width = self.table_width
        return tab

    def multiline_text(self, **kwargs):
        """
        多行文本模式
        :param kwargs: None 为了统一接口方便映射
        :return: AwesomeTable
        """
        if not kwargs:
            kwargs = self.data.get("multiline_text")
        max_num_of_rows = kwargs["max_num_of_rows"]
        min_num_of_rows = kwargs["min_num_of_rows"]
        num = random.randint(min_num_of_rows, max_num_of_rows)
        multi_text = []
        for i in range(num):
            multi_text.append(str(i + 1) + "." + self.rand_text(random.randint(10, 20)))
        tab = AwesomeTable()
        tab.add_rows([[x] for x in multi_text])
        tab.table_width = self.table_width
        tab.vrules = prettytable.FRAME
        tab.hrules = prettytable.FRAME

        tab.align = "l"
        has_title = random.random() < kwargs["has_title_raito"]
        if not has_title:
            return tab
        title_tab = AwesomeTable()
        title = self.rand_text(random.choice((4, 6, 8)), place_holder="key")
        title_tab.add_row([title])
        tab.table_width = self.table_width - title_tab.table_width + 1
        return hstack(title_tab, tab)

    def single_key_value(self, **kwargs):
        """
        单个键值对
        :param kwargs: None 为了统一接口方便映射
        :return: AwesomeTable
        """
        key = self.rand_text(6, place_holder="key")
        value = self.rand_text(random.randint(8, 16), place_holder="value")
        key_tab = AwesomeTable()
        key_tab.add_row([key])
        key_tab.min_width = self.min_width_of_cell
        val_tab = AwesomeTable()
        val_tab.add_row([value])
        val_tab.table_width = self.table_width - key_tab.table_width + 1
        val_tab.min_width = self.min_width_of_cell
        return hstack(key_tab, val_tab)

    def multiple_key_value_pairs(self, **kwargs):
        """
        多个键值对
        :param kwargs: None 为了统一接口方便映射
        :return: AwesomeTable
        """
        if not kwargs:
            kwargs = self.data.get("multiple_key_value_pairs")
        min_num_of_pairs = kwargs["min_num_of_pairs"]
        max_num_of_pairs = kwargs["max_num_of_pairs"]
        num = random.randint(min_num_of_pairs, max_num_of_pairs)
        pairs = []
        for _ in range(num):
            pairs.append(self.rand_text(6, place_holder="key"))
            pairs.append(self.rand_text(random.randint(8, 16), place_holder="value"))
        tab = AwesomeTable()
        tab.add_row(pairs)
        tab.min_width = self.min_width_of_cell
        return tab

    def single_key_multiple_values(self, **kwargs):
        """
        单键多值
        :param kwargs: None 为了统一接口方便映射
        :return: AwesomeTable
        """
        if not kwargs:
            kwargs = self.data.get("single_key_multiple_values")
        max_options = kwargs["max_options"]
        min_options = kwargs["min_options"]
        num = random.randint(min_options, max_options)
        choices = []

        for _ in range(num):
            choices.append(
                "[x]" + self.rand_text(random.randint(4, 8), place_holder="value")
            )

        key = self.rand_text(6, place_holder="key")
        key_tab = AwesomeTable()
        key_tab.add_row([key])
        key_tab.min_width = self.min_width_of_cell
        val_tab = AwesomeTable()
        val_tab.add_row(choices)
        val_tab.vrules = prettytable.FRAME
        val_tab.table_width = self.table_width - key_tab.table_width + 1
        return hstack(key_tab, val_tab)

    def multiple_rows_multiple_columns(self, **kwargs):
        """
        多行多列
        :param kwargs: None 为了统一接口方便映射
        :return: AwesomeTable
        """
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
                table[i][0] = self.rand_text(random.randint(2, 6), place_holder="key")
        tab = AwesomeTable()
        tab.add_rows(table)

        if random.random() < kwargs["vrules_all_ratio"]:
            tab.vrules = prettytable.ALL
        else:
            tab.vrules = prettytable.FRAME
        if random.random() < kwargs["hrules_all_ratio"]:
            tab.hrules = prettytable.ALL
        else:
            tab.hrules = prettytable.FRAME

        if self.table_width > 0:
            tab.table_width = self.table_width
        tab.min_width = self.min_width_of_cell
        return str(tab)

    def complex(self, **kwargs):
        """
        复杂表头
        :param kwargs: None 为了统一接口方便映射
        :return: AwesomeTable
        """
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

        dic = self.rand_dict(depth, cols, rows)
        t2b = random.random() > kwargs["left_to_right_ratio"]  # 从上到下的概率

        if t2b:
            if random.random() < kwargs["fixed_width_ratio"]:
                max_width = max(self.table_width // (cols**depth), 12)
                return from_dict(dic, t2b, max_width)
            return from_dict(dic, t2b)

        if random.random() < kwargs["fixed_width_ratio"]:
            max_width = max(self.table_width // (depth + rows), 12)  # 保证同宽度的补丁
            return from_dict(dic, t2b, max_width)
        return from_dict(dic, t2b)

    def cross_rows_cross_cols(self, **kwargs):
        """
        跨行跨列的情况
        :param kwargs: None 为了统一接口方便映射
        :return: AwesomeTable
        """
        if not kwargs:
            kwargs = self.data.get("cross_rows_cross_cols")
        nob = random.randint(2, kwargs.get("max_num_of_blocks", 2))
        blocks = []
        blocks_width = self.table_width // nob  # 平均宽度

        for _ in range(nob):
            noc = random.randint(2, kwargs.get("max_num_of_cols", 2))
            nor = random.randint(2, kwargs.get("max_num_of_rows", 2))
            block = self.rand_table(noc, nor, blocks_width, random.randint(0, 3))
            blocks.append(block)
        return hstack(blocks)
