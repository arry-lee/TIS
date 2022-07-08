import os.path
import random
import time
from itertools import cycle

import cv2
from tqdm import tqdm
from faker import Faker

from awesometable.layout import HorLayout as H
from awesometable.layout import VerLayout as V
from awesometable.layout import TextBlock, FlexTable
from awesometable.table2pdf import render_pdf

from post_processor.label import log_label
from post_processor.background import add_background_data, add_to_paper
from awesometable.table2image import table2image

from fs_settings import *
from post_processor.paper import Paper

COLUMN_WIDTH = (PAPER_WIDTH - PAPER_OFFSET * 2 - HOR_GAP_WIDTH) // 2
PAGE_WIDTH = PAPER_WIDTH - PAPER_OFFSET * 2
paper = Paper(PAPER_WIDTH, offset_p=PAPER_OFFSET)
COL_HEIGHT = paper.height - PAPER_OFFSET * 2

f = Faker(providers=["fs_provider"])
hit = lambda r: random.random() < r


class FSTable(FlexTable):
    """财务报表

    width=None,  宽度像素
    rows=None, 行数
    cols=None, 列数
    indent=False, 缩进
    font_size=40, 字号
    complex_header=False, 多级表头
    double_column=False,  双栏表格
    large_gap=False, index列与data列间距大
    dollar_column=False,  美元符号列
    lno_column=False  行号列
    style 风格
    """

    style = "striped"

    def __init__(
        self,
        width=None,
        rows=None,
        cols=None,
        indent=False,
        font_size=40,
        price_width=None,
        complex_header=False,
        double_column=False,
        large_gap=False,
        dollar_column=False,
        lno_column=False,
        **kwargs
    ):

        super().__init__(width, font_size, **kwargs)
        if rows is None:
            rows = random.randint(DEFAULT_ROW_MIN, DEFAULT_ROW_MAX)
        if cols is None:
            cols = random.randint(DEFAULT_COL_MIN, DEFAULT_COL_MAX)
            indent = hit(0.5)

        if price_width is None:
            _default_price_width = DEFAULT_NUM_MIN
        else:
            _default_price_width = price_width

        self.rows = rows
        self.cols = cols
        indexes = f.indexes(rows)
        columns = f.columns(cols)
        if dollar_column:
            columns[1] = "USD"
        elif lno_column:
            columns[1] = "No."

        self.add_row(columns)
        _max_price_width = 0

        subtitle_rows = f.subtitle_lines(rows, DEFAULT_INDENT_MIN, DEFAULT_INDENT_MAX)

        for lno, i in enumerate(indexes):
            row = []
            for _ in columns:
                p = f.price(_default_price_width, True, False, empty_ratio=0.1)
                row.append(p)
                _max_price_width = max(_max_price_width, len(p))
            if dollar_column:
                row[1] = "$"

            if indent:
                if lno in subtitle_rows:
                    row[0] = f.subtitle()
                    row[1:] = [""] * (cols - 1)
                else:
                    row[0] = i.capitalize()
            else:
                row[0] = i.capitalize()

            if lno_column:
                row[1] = lno

            if double_column:
                if indent:
                    if lno in subtitle_rows:
                        row[cols // 2] = f.subtitle()
                    else:
                        row[cols // 2] = f.index()
                else:
                    row[cols // 2] = f.index()
            self.add_row(row)

        self.align = "r"
        self._align["Field 1"] = "l"
        if hit(0.5):
            self.valign = "m"
        else:
            self.valign = "t"
        self.min_width = _max_price_width
        self.max_width = 20
        self._max_cell_width = _max_price_width
        if double_column:
            self._align["Field %d" % (cols // 2 + 1)] = "l"

        self.large_gap = large_gap
        self.complex_header = complex_header

    def __str__(self):
        if self.large_gap:
            self.widths = []
            tw = self._max_table_width - self.cols - 1
            # 按照10等份，后面的各取1份，剩下的给前面
            nw = max(self._max_cell_width + 2, tw // 10)
            self.widths = [nw] * (self.cols - 1)
            self.widths.insert(0, tw - nw * (self.cols - 1))
        s = self.get_string()
        if self.complex_header:
            s = f.build_complex_header(s, self._rows[0])
        return s


class FSText(TextBlock):
    def __init__(
        self, width=COLUMN_WIDTH, sentence=3, indent=4, font_size=TEXT_FONT_SIZE
    ):
        super().__init__(f.paragraph(sentence), width, indent, font_size=font_size)


class FSTitle(TextBlock):
    count = 1

    def __init__(
        self, width=COLUMN_WIDTH, fill=TITLE_COLOR, font_size=TITLE_FONT_SIZE, **kwargs
    ):
        title = str(self.count) + ". " + f.subtitle()
        super().__init__(title, width, font_size=font_size, fill=fill, **kwargs)
        FSTitle.count += 1


class FSLongTextTable(FlexTable):
    def __init__(self, width=PAGE_WIDTH, font_size=TEXT_FONT_SIZE, **kwargs):
        super().__init__(width=width, font_size=font_size, **kwargs)
        if hit(0.5):
            self.add_row(["Exhibit No.", "DESCRIPTION"])
            pno = random.randint(100, 900)
            for i in range(10):
                pno += 1
                d = random.randint(1, 4)
                no = random.choice("abcdef")
                x = "%d.%d%s" % (pno, d, no)
                self.add_row([x, f.paragraph(random.randint(2, 4))])
            self.max_width = int(0.8 * self._max_table_width)
            self.min_width = 11
            self.align = "l"
        else:
            self.add_row(["Item", "Page"])
            pno = random.randint(1, 200)
            for i in range(10):
                n = random.randint(1, 10)
                pno += n
                self.add_row([f.paragraph(random.randint(1, 4)), pno])
            self.max_width = int(0.8 * self._max_table_width)
            self._align = {"Field 1": "l", "Field 2": "r"}

    def get_image(self):
        return table2image(
            str(self),
            line_pad=4,
            font_size=self.font_size,
            vrules=None,
            hrules=None,
            style="simple",
            bold_pattern=None,
            border="",
            align=None,
        )


class LayoutDesigner(object):
    def __init__(self, table_generator=None, text_generator=None, title_generator=None):
        self.ta = table_generator or FSTable
        self.te = text_generator or FSText
        self.ti = title_generator or FSTitle
        self.tt = FSLongTextTable

    @staticmethod
    def template(sequence, height, gap=VER_GAP_HEIGHT):
        col = []
        h = 0
        for klass in cycle(sequence):
            t = klass()
            h += t.height
            if h <= height:
                col.append(t)
                h += gap
            else:
                h -= t.height
                break
        if col and isinstance(col[-1], FSTitle):
            col.pop()
            FSTitle.count -= 1

        while True:
            t = FSText(sentence=3)
            h += t.height
            if h <= height:
                col.append(t)
                h += gap
            else:
                break
        return col

    def _layout0(self):
        # 双栏
        l = self.template([self.ti, self.te, self.ta], COL_HEIGHT)
        r = self.template([self.ti, self.te, self.ta], COL_HEIGHT)
        out = H(
            [
                V(l, COLUMN_WIDTH, gaps=VER_GAP_HEIGHT),
                V(r, COLUMN_WIDTH, gaps=VER_GAP_HEIGHT),
            ],
            COLUMN_WIDTH,
            gaps=HOR_GAP_WIDTH,
        )
        self.ti.count = 1
        return out

    def _layout1(self):
        # 双栏插图
        out_list = [
            H([self.te(), self.te()], COLUMN_WIDTH, gaps=HOR_GAP_WIDTH),
            self.ta(
                PAGE_WIDTH,
                rows=random.randint(8, 13),
                cols=random.randint(5, 8),
                double_column=hit(1),
                indent=True,
                large_gap=hit(0.5),
                dollar_column=hit(0.5),
                lno_column=hit(0.5),
                complex_header=hit(0.5),
            ),
        ]
        out = V(out_list, PAGE_WIDTH, gaps=VER_GAP_HEIGHT)
        hmax = COL_HEIGHT - out.height - VER_GAP_HEIGHT

        l = self.template([self.te, self.ta], hmax)
        r = self.template([self.te, self.ta], hmax)
        h = H(
            [
                V(l, COLUMN_WIDTH, gaps=VER_GAP_HEIGHT),
                V(r, COLUMN_WIDTH, gaps=VER_GAP_HEIGHT),
            ],
            COLUMN_WIDTH,
            gaps=HOR_GAP_WIDTH,
        )
        out_list.append(h)
        return V(out_list, PAGE_WIDTH, gaps=VER_GAP_HEIGHT)

    def _layout2(self):
        # 单栏
        l = []
        if hit(0.5):
            l.append(self.ti())
        l.append(self.te())
        l.append(
            self.ta(
                width=PAGE_WIDTH,
                rows=random.randint(8, 15),
                cols=random.randint(5, 10),
                complex_header=hit(0.5),
                large_gap=True,
                indent=True,
                double_column=hit(0.5),
            )
        )

        lv = V(l, PAGE_WIDTH, gaps=VER_GAP_HEIGHT)
        hmax = COL_HEIGHT - lv.height
        while True:
            t = self.te(sentence=random.randint(5, 10))
            if t.height <= hmax - VER_GAP_HEIGHT:
                l.append(t)
                hmax = hmax - VER_GAP_HEIGHT - t.height
            else:
                break
            t = self.ta(
                rows=random.randint(4, 6),
                cols=None,
                complex=hit(0),
                double_column=hit(0.5),
            )
            if t.height <= hmax - VER_GAP_HEIGHT:
                l.append(t)
                hmax = hmax - VER_GAP_HEIGHT - t.height
            else:
                continue
        l.append(self.te(sentence=random.randint(5, 10)))

        out = V(l, PAGE_WIDTH, gaps=VER_GAP_HEIGHT)
        self.ti.count = 1
        return out

    def _layout3(self):
        return self.tt()

    def _layout4(self):
        # 普通单个财务报表
        return self.ta(
            rows=random.randint(20, 30),
            cols=random.randint(4, 12),
            double_column=hit(0.5),
            complex_header=hit(0.5),
            lno_column=hit(0.5),
            dollar_column=hit(0.2),
            price_width=7,
            large_gap=False,
            indent=True,
        )

    def create(self, type):
        if type == 0:
            return self._layout0()
        elif type == 1:
            return self._layout1()
        elif type == 2:
            return self._layout2()
        elif type == 3:
            return self._layout3()
        elif type == 4:
            return self._layout4()

    def _toggle_style(self):
        self.ta.style = random.choice(["striped", "other", "simple"])

    def run(self, batch, output_dir="data/financial_statement_en_sp"):
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        err = 0
        cnt = 0
        pbar = tqdm(total=batch)
        pbar.set_description("Generating")
        while cnt < batch:
            self._toggle_style()
            try:
                image_data = self.create(cnt % 5).get_image()
            except ValueError:
                err += 1
                print(err)
                continue

            if cnt % 5 != 4:
                image_data = add_to_paper(image_data, paper)
            else:
                image_data = add_background_data(image_data, paper.image, offset=100)

            fn = "0" + str(int(time.time() * 1000))[5:]
            cv2.imwrite(os.path.join(output_dir, "%s.jpg" % fn), image_data["image"])
            render_pdf(image_data,os.path.join(output_dir, "%s.pdf" % fn))
            log_label(
                os.path.join(output_dir, "%s.txt" % fn), "%s.jpg" % fn, image_data
            )
            cnt += 1
            pbar.update(1)
        pbar.close()


if __name__ == "__main__":
    d = LayoutDesigner()
    d.run(50)
