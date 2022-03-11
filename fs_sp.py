import os.path
import random
import time
from itertools import cycle

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

    def __init__(self, w=col_width, rows=None, complex=False,
                 double_column=False,large_gap=False, font_size=44, **kwargs):
        super().__init__(w, font_size, **kwargs)
        random_price = lambda:'{:,}'.format(random.randint(100, 1000))
        type = random.choice(("CONSOLIDATED INCOME STATEMENT","Consolidated Balance Sheet"))
        self.fst = FinancialStatementTable(type, "en",
                                           random_price)
        t = self.fst.metatable(auto_ratio=0, brace_ratio=0, fill_ratio=0.9,
                               note_ratio=0)
        self.can_complex = complex
        # 先取columns
        if double_column:
            row = t._rows[0]
            row = row + row[1:]
            self.add_row(row)
        elif complex or len(t._rows[0]) <= 4:
            row = t._rows[0]
            self.add_row(row)

        if not rows:  # 设置行数
            rows = random.randint(4, 5) #默认范围
        s = random.randint(1, len(t._rows) - rows)  # 随机起点
        for x in t[s:s + rows]._rows:
            if double_column:
                x = x + x[1:]
            self.add_row(x)
        self.align = 'r'  # 统一右对齐
        self.min_width = 12
        self.max_width = 20
        self._align['Field 1'] = 'l'  # 第一列左对齐

        self.large_gap = large_gap and len(self._rows[0])<=5


    def __str__(self):
        if self.large_gap: # index 与 data 距离较大
            self.widths = []
            tw = self.max_table_width-len(self._rows[0])-1
            lens = len(self._rows[0])
            nw = tw//10    # 按照10等份，后面的各取1份，剩下的给前面
            self.widths = [nw]*(lens-1)
            self.widths.insert(0,tw-nw*(lens-1))
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

    def __init__(self, width=col_width, fill=(10, 10, 10), font_size=48,
                 **kwargs):
        super().__init__(str(self.cnt) + '. ' + self.faker.paragraph(1),
                         width, font_size=font_size, fill=fill,
                         font_path='simfang.ttf', **kwargs)
        _NoteGenerator.cnt += 1


class _LongTextTable(FlexTable):
    faker = faker.Faker()
    def __init__(self, w=page_width,font_size=40, **kwargs):
        super().__init__(w=w,font_size=font_size, **kwargs)
        if hit(0.5):
            self.add_row(['Exhibit No.','DESCRIPTION'])
            s = random.randint(100,900)
            for i in range(18):
                s += 1
                d = random.randint(1,4)
                no = random.choice("abcdef")
                x = "%d.%d%s"%(s,d,no)
                self.add_row([x,self.faker.paragraph(random.randint(6,8))])
            self.max_width = int(0.9 * self._max_table_width)
            self.align = 'l'
        else:
            self.add_row(['Item', 'Page'])
            s = random.randint(1, 200)
            for i in range(20):
                n = random.randint(1,10)
                s+=n
                self.add_row([self.faker.paragraph(random.randint(1,4)),s])
            self.max_width = int(0.9 * self._max_table_width)
            self._align = {"Field 1":"l","Field 2":"r"}
        self.table_width = page_width

    def get_image(self):
        return table2image(str(self), font_size=self.font_size, vrules=None,
                           hrules=None, style='simple',bold_pattern=None,border='',align=None)


class LayoutDesigner(object):
    faker = faker.Faker()
    def __init__(self, table_generator=None, text_generator=None):
        self.table_generator = table_generator or _TableGenerator
        self.text_generator = text_generator or _TextGenerator
        self.title_generator = _TitleGenerator
        self.note_generator = _NoteGenerator
        self.paper = Paper(3000, offset_p=400)
        self.col_height = self.paper.height - offset_p * 2
        self.ltt = _LongTextTable

    @staticmethod
    def template(squence,hmax,gap=40):
        col = []
        h = 0
        for klass in cycle(squence):
            t = klass()
            h += t.height
            if h<=hmax:
                col.append(t)
                h+=gap
            else:
                h -= t.height
                break
        if col and isinstance(col[-1],_TitleGenerator):
            col.pop()
            _TitleGenerator.cnt-=1

        while True:
            t = _TextGenerator(sentence=3)
            h += t.height
            if h <= hmax:
                col.append(t)
                h+=gap
            else:
                break
        return col

    def random_layout0(self):
        # 双栏
        l = self.template([self.title_generator,self.text_generator,self.table_generator],self.col_height)
        r = self.template([self.title_generator,self.text_generator,self.table_generator],self.col_height)
        out = H([V(l, col_width, gaps=40), V(r, col_width, gaps=40)], col_width,gaps=80)
        self.title_generator.cnt = 1
        return out

    def random_layout1(self):
        # 双栏插图
        out_list = [H([self.text_generator(), self.text_generator()], col_width,gaps=80),
                    self.table_generator(page_width,rows=random.randint(8,15),double_column=hit(0.5),large_gap=hit(0.5),complex=hit(0.5))
                    ]
        out = V(out_list, page_width, gaps=40)
        hmax = self.col_height - out.height - 40

        l = self.template([self.text_generator,self.table_generator],hmax)
        r = self.template([self.text_generator, self.table_generator], hmax)
        h = H([V(l, col_width, gaps=40), V(r, col_width, gaps=40)], col_width,gaps=80)
        out_list.append(h)
        return V(out_list, page_width, gaps=40)

    def random_layout2(self):
        # 单栏
        l = []
        if hit(0.5):
            l.append(self.title_generator())
        l.append(self.text_generator())
        l.append(self.table_generator(w=page_width,rows=random.randint(8, 15),
                                      complex=hit(0.5),
                                      large_gap=True,
                                      double_column=hit(0.5)))

        lv = V(l, page_width, gaps=40)
        hmax = self.col_height - lv.height
        while True:
            t = self.text_generator(sentence=random.randint(5, 10))
            if t.height <= hmax - 40:
                l.append(t)
                hmax = hmax - 40 - t.height
            else:
                break
            t = self.table_generator(rows=random.randint(4, 6),
                                     complex=hit(0),
                                     double_column=hit(0.5))
            if t.height <= hmax - 40:
                l.append(t)
                hmax = hmax - 40 - t.height
            else:
                continue
        l.append(self.text_generator(sentence=random.randint(5, 10)))

        out = V(l, page_width, gaps=40)
        self.title_generator.cnt = 1
        return out

    def random_layout3(self):
        x = self.ltt()
        return x

    def random_layout4(self):
        # 普通单个财务报表
        title = random.choice(["CONSOLIDATED INCOME STATEMENT",
                               "Consolidated Balance Sheet",
                               "Consolidated Cash Flow Statement"])
        return FinancialStatementTable(title,'en')

    def create(self, type):
        self.cnt = 0
        if type == 0:
            return self.random_layout0()
        elif type == 1:
            return self.random_layout1()
        elif type == 2:
            return self.random_layout2()
        elif type == 3:
            return self.random_layout3()
        elif type == 4:
            return self.random_layout4()

    def toggle_style(self):
        self.table_generator.style = random.choice(["striped","other","simple"])


    def run(self, batch,output_dir="data/financial_statement_en_sp"):
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        err = 0
        for i in trange(batch):
            self.toggle_style()
            try:
                image_data = self.create(i%5).get_image()
            except ValueError:
                err+=1
                print(err)
                continue

            if i%5!=4:
                image_data = add_to_paper(image_data, self.paper)
            fn = "0" + str(int(time.time() * 1000))[5:]
            cv2.imwrite(os.path.join(output_dir, "%s.jpg" % fn),
                        image_data["image"])
            log_label(
                os.path.join(output_dir, "%s.txt" % fn), "%s.jpg" % fn,
                image_data
            )



if __name__ == "__main__":
    d = LayoutDesigner()
    d.run(20)