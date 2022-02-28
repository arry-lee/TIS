import os.path
import random
import time

import cv2
import faker
from tqdm import trange

from fs_data import FinancialStatementTable, hit
from layout import HorLayout as H
from layout import VerLayout as V
from layout import TextBlock,FlexTable
from post_processor.A4 import Paper

from post_processor.label import log_label, show_label
from post_processor.background import add_to_paper
from table2image import table2image

width=3000
offset_p=400
gap_width = 80
col_width = (width-offset_p*2-gap_width)//2

page_width = width-offset_p*2

font_size = 40
# table_width = col_width//font_size*2

# print(col_width,page_width)

class _TableGenerator(FlexTable):
    style = "striped"
    def __init__(self, w=col_width,font_size=28, **kwargs):
        super().__init__(w, font_size, **kwargs)
        random_price = lambda:'{:,}'.format(random.randint(100, 1000))
        self.fst = FinancialStatementTable("Consolidated Balance Sheet", "en",random_price)
        t = self.fst.metatable(auto_ratio=0, brace_ratio=0, fill_ratio=1, note_ratio=0)
        s = random.choice([0, 2, 3, 4, 5])
        r = random.randint(5, 15)
        for x in t[s:s+r]._rows:
            self.add_row(x)
        self.align = 'r'
        self.min_width = 5
        self._align['Field 1'] = 'l'


class _TextGenerator(TextBlock):
    faker = faker.Faker()
    def __init__(self, width=col_width,sentence=10,font_size=50):
        super().__init__(self.faker.paragraph(sentence), width, indent=4,font_size=font_size)


class DoubleColumnFST(object):
    def __init__(self, table_generator=None, text_generator=None):
        self.table_generator = table_generator or _TableGenerator
        # 统一风格
        if hit(0.5):
            self.table_generator.style = "other"
        self.text_generator = text_generator or _TextGenerator
        self.paper = Paper(3000, offset_p=400)
        self.col_height = self.paper.height-offset_p*2

    def random_layout(self):
        table_nums = random.randint(3, 4)
        ln = table_nums // 2
        rn = table_nums - ln

        l, r = [], []
        for i in range(ln):
            l.append(self.text_generator())
            l.append(self.table_generator())
        l.append(self.text_generator())
        lv = V(l,col_width,gaps=40)
        hmax = self.col_height-lv.height
        while True:
            t = self.text_generator(sentence=10)
            if t.height<=hmax-40:
                l.append(t)
                hmax = hmax-40-t.height
            else:
                break

        for i in range(rn):
            r.append(self.text_generator())
            r.append(self.table_generator())
        rv = V(r,col_width,gaps=40)
        hmax = self.col_height-rv.height
        while True:
            t = self.text_generator(sentence=10)
            if t.height<=hmax-40:
                r.append(t)
                hmax = hmax-40-t.height
            else:
                break

        out = H([V(l,col_width,gaps=40), V(r,col_width,gaps=40)],col_width,gaps=80)
        return out

    def random_layout2(self):
        if hit(0.5):
            r = [self.text_generator(), self.table_generator()]
        else:
            r = [self.table_generator(),self.text_generator()]

        out_list = [H([self.text_generator(), self.text_generator()],col_width,gaps=80),
                self.table_generator(page_width),
                 ]
        out = V(out_list,page_width,gaps=40)
        hmax = self.col_height - out.height-40
        l = [self.text_generator(), self.table_generator()]
        lv = V(l,col_width,gaps=40)
        _hmax = hmax-lv.height
        while True:
            t = self.text_generator(sentence=5)
            if t.height<=_hmax-40:
                l.append(t)
                _hmax = _hmax-40-t.height
            else:
                break
        rv = V(r, col_width, gaps=40)
        _hmax = hmax-rv.height
        while True:
            t = self.text_generator(sentence=5)
            if t.height<=_hmax-40:
                r.append(t)
                _hmax = _hmax-40-t.height
            else:
                break

        h = H([V(l,col_width,gaps=40),V(r,col_width,gaps=40)],col_width,gaps=80)
        out_list.append(h)
        return V(out_list,page_width,gaps=40)

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
            image_data = self.create(i % 2).get_image()
            image_data = add_to_paper(image_data,self.paper)
            fn = "0" + str(int(time.time() * 1000))[5:]
            cv2.imwrite(os.path.join(output_dir, "%s.jpg" % fn), image_data["image"])
            log_label(
                os.path.join(output_dir, "%s.txt" % fn), "%s.jpg" % fn, image_data
            )


# class PaperFactory(object):
#     width = 3000
#     offset_p = 400
#     gap_width = 80
#     col_width = (width - offset_p * 2 - gap_width) // 2
#
#     font_size = 40
#     def __init__(self,width,offset_p,gap_width):
#         self.paper = Paper(width,offset_p=offset_p)
#         page_width = width - offset_p * 2
#         page_height = self.paper.height
#
if __name__ == "__main__":
    d = DoubleColumnFST()
    d.run(20)

