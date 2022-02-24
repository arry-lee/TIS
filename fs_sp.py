import os.path
import random
import time

import cv2
import faker
from tqdm import trange

from fs_data import FinancialStatementTable, hit
from layout import HorLayout as H
from layout import VerLayout as V
from layout import TextBlock

from post_processor.label import log_label, show_label

from table2image import table2image


class _TableGenerator(object):
    style = "striped"
    def __init__(self, w=40):
        random_price = lambda:'{:,}'.format(random.randint(100, 1000))
        self.fst = FinancialStatementTable("Consolidated Balance Sheet", "en",random_price)

        t = self.fst.metatable(auto_ratio=0, brace_ratio=0, fill_ratio=1, note_ratio=0)
        t.max_width = 15
        t.min_width = 4
        t.max_table_width = w
        t.align = "r"
        t._align["Field 1"] = "l"
        self._table = t

    @property
    def table(self):
        s = random.choice([0,2,3,4,5])
        r = random.randint(3,6)
        return self._table[s:s+r]

    @property
    def table_width(self):
        return self._table.table_width

    @table_width.setter
    def table_width(self, val):
        self._table.table_width = val

    def get_image(self, **kwargs):
        return table2image(self.table,vrules=None,hrules=None,style=self.style)


class _TextGenerator(TextBlock):
    faker = faker.Faker()

    def __init__(self, width=38):
        super().__init__(self.faker.paragraph(8), width, indent=4)


class DoubleColumnFST(object):
    def __init__(self, table_generator=None, text_generator=None):
        self.table_generator = table_generator or _TableGenerator
        # 统一风格
        if hit(0.5):
            self.table_generator.style = "other"
        self.text_generator = text_generator or _TextGenerator

    def random_layout(self):
        table_nums = random.randint(3, 4)
        ln = table_nums // 2
        rn = table_nums - ln

        l, r = [], []
        for i in range(ln):
            l.append(self.text_generator())
            l.append(self.table_generator())
        l.append(self.text_generator())
        if ln < rn:
            l.append(self.text_generator())
        for i in range(rn):
            r.append(self.text_generator())
            r.append(self.table_generator())
        # r.append(self.text_generator())
        out = H([V(l), V(r)])
        return out

    def random_layout2(self):
        if hit(0.5):
            l = [self.text_generator(), self.table_generator()]
        else:
            l = [self.table_generator(),self.text_generator()]

        out = V(
            [
                H([self.text_generator(), self.text_generator()]),
                self.table_generator(),
                H(
                    [
                        V([self.text_generator(), self.text_generator()]),
                        V(l),
                    ]
                ),
            ]
        )
        return out

    def create(self, type):
        self.cnt = 0
        if type == 1:
            return self.random_layout()
        elif type == 0:
            return self.random_layout2()

    def run(self, batch):
        output_dir = "data/financial_statement_en_sp"
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        for i in trange(batch):
            image_data = self.create(i % 2).get_image(offset=25)

            fn = "0" + str(int(time.time() * 1000))[5:]
            cv2.imwrite(os.path.join(output_dir, "%s.jpg" % fn), image_data["image"])
            log_label(
                os.path.join(output_dir, "%s.txt" % fn), "%s.jpg" % fn, image_data
            )


if __name__ == "__main__":
    d = DoubleColumnFST()
    d.run(25)

