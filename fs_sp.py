import os.path
import random
import time

import cv2
import faker
from tqdm import trange

from fs_data import FinancialStatementTable, hit
from layout import HorLayout as H
from layout import VerLayout as V
from layout import TextBlock, FlexTable
from post_processor.A4 import Paper

from post_processor.label import log_label, show_label
from post_processor.background import add_to_paper
from table2image import table2image

width = 3000
offset_p = 400
gap_width = 80
col_width = (width - offset_p * 2 - gap_width) // 2

page_width = width - offset_p * 2

font_size = 40


# table_width = col_width//font_size*2


# 这里定义业务相关的表和文本
# KEEP DRY
# todo 财务的表格已经在FST中实现了，没有tablewidth选项导致不能兼容
class _TableGenerator(FlexTable):
    style = "striped"
    faker = faker.Faker()
    def __init__(self, w=col_width, rows=None,complex=False, font_size=44, **kwargs):
        super().__init__(w, font_size, **kwargs)
        random_price = lambda:'{:,}'.format(random.randint(100, 1000))
        self.fst = FinancialStatementTable("Consolidated Balance Sheet", "en",random_price)
        t = self.fst.metatable(auto_ratio=0, brace_ratio=0, fill_ratio=1,
                               note_ratio=0)
        self.can_complex = complex
        # 先取columns
        if complex or len(t._rows[0])<=4:
            self.add_row(t._rows[0])
        else:
            pass
            # self.add_row([self.faker.word() for x in t._rows[0]])
        if not rows:  # 设置行数
            rows = random.randint(3, 6)
        s = random.randint(1, len(t._rows) - rows)  # 随机起点
        for x in t[s:s + rows]._rows:
            self.add_row(x)
        self.align = 'r'  # 统一右对齐
        self.min_width = 12
        self.max_width = 20
        self._align['Field 1'] = 'l'  # 第一列左对齐


    def __str__(self):
        _string = self.get_string()
        if self.can_complex:
            _string = self.fst.build_complex_header(_string, cc=self._rows[0])
        return _string


class _TextGenerator(TextBlock):
    faker = faker.Faker()

    def __init__(self, width=col_width, sentence=10, font_size=52):
        super().__init__(self.faker.paragraph(sentence), width, indent=4,
                         font_size=font_size)


class _TitleGenerator(TextBlock):
    faker = faker.Faker()
    cnt = 1

    def __init__(self, width=col_width, fill=(235, 119, 46), font_size=60,
                 **kwargs):
        super().__init__(str(self.cnt) + '. ' + self.faker.word().upper(),
                         width, font_size=font_size, fill=fill, **kwargs)
        _TitleGenerator.cnt += 1

class _NoteGenerator(TextBlock):
    faker = faker.Faker()
    cnt = 1
    def __init__(self, width=col_width, fill=(10,10,10), font_size=48,
                 **kwargs):
        super().__init__(str(self.cnt) + '. ' + self.faker.paragraph(1),
                         width, font_size=font_size, fill=fill,font_path='simfang.ttf', **kwargs)
        _NoteGenerator.cnt += 1

class DoubleColumnFST(object):
    faker = faker.Faker()

    def __init__(self, table_generator=None, text_generator=None):
        self.table_generator = table_generator or _TableGenerator
        # 统一风格

        self.text_generator = text_generator or _TextGenerator
        self.title_generator = _TitleGenerator
        self.note_generator = _NoteGenerator
        self.paper = Paper(3000, offset_p=400)
        self.col_height = self.paper.height - offset_p * 2

    def random_layout(self):
        # 双栏
        table_nums = random.randint(3, 4)
        ln = table_nums // 2
        rn = table_nums - ln
        l, r = [], []
        for i in range(ln):
            l.append(self.title_generator())
            l.append(self.text_generator())
            l.append(self.table_generator())
        l.append(self.text_generator())
        lv = V(l, col_width, gaps=40)
        hmax = self.col_height - lv.height
        while True:
            t = self.text_generator(sentence=10)
            if t.height <= hmax - 40:
                l.append(t)
                hmax = hmax - 40 - t.height
            else:
                break

        for i in range(rn):
            r.append(self.title_generator())
            r.append(self.text_generator())
            r.append(self.table_generator())
        rv = V(r, col_width, gaps=40)
        hmax = self.col_height - rv.height
        while True:
            t = self.text_generator(sentence=10)
            if t.height <= hmax - 40:
                r.append(t)
                hmax = hmax - 40 - t.height
            else:
                break

        out = H([V(l, col_width, gaps=40), V(r, col_width, gaps=40)], col_width,
                gaps=80)
        self.title_generator.cnt = 1
        return out

    def random_layout2(self):
        # 双栏插图
        if hit(0.5):
            r = [self.text_generator(), self.table_generator()]
        else:
            r = [self.table_generator(), self.text_generator()]

        out_list = [H([self.text_generator(), self.text_generator()], col_width,
                      gaps=80),
                    self.table_generator(page_width),
                    ]
        out = V(out_list, page_width, gaps=40)
        hmax = self.col_height - out.height - 40
        l = [self.text_generator(), self.table_generator()]
        lv = V(l, col_width, gaps=40)
        _hmax = hmax - lv.height
        while True:
            t = self.text_generator(sentence=5)
            if t.height <= _hmax - 40:
                l.append(t)
                _hmax = _hmax - 40 - t.height
            else:
                break
        rv = V(r, col_width, gaps=40)
        _hmax = hmax - rv.height
        while True:
            t = self.text_generator(sentence=5)
            if t.height <= _hmax - 40:
                r.append(t)
                _hmax = _hmax - 40 - t.height
            else:
                break

        h = H([V(l, col_width, gaps=40), V(r, col_width, gaps=40)], col_width,
              gaps=80)
        out_list.append(h)
        return V(out_list, page_width, gaps=40)

    def random_layout3(self):
        # 单栏

        l = []
        l.append(self.title_generator())
        l.append(self.text_generator())
        l.append(self.table_generator(rows=random.randint(10,15),complex=True))

        lv = V(l, page_width, gaps=40)
        hmax = self.col_height - lv.height
        while True:
            t = self.text_generator(sentence=5)
            if t.height <= hmax - 40:
                l.append(t)
                hmax = hmax - 40 - t.height
            else:
                break

        out = V(l, page_width, gaps=40)
        self.title_generator.cnt = 1
        return out

    def create(self, type):
        self.cnt = 0
        if type == 1:
            return self.random_layout()
        elif type == 0:
            return self.random_layout2()
        elif type == 2:
            return self.random_layout3()

    def toggle_style(self):
        if self.table_generator.style == "striped":
            self.table_generator.style = "other"
        else:
            self.table_generator.style = "striped"

    def run(self, batch):
        output_dir = "data/financial_statement_en_sp"
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        for i in trange(batch):
            self.toggle_style()
            image_data = self.create(i%3).get_image()
            image_data = add_to_paper(image_data, self.paper)
            fn = "0" + str(int(time.time() * 1000))[5:]
            cv2.imwrite(os.path.join(output_dir, "%s.jpg" % fn),
                        image_data["image"])
            log_label(
                os.path.join(output_dir, "%s.txt" % fn), "%s.jpg" % fn,
                image_data
            )


# class Manager(object):
#     co
#
if __name__ == "__main__":
    d = DoubleColumnFST()
    d.run(20)
