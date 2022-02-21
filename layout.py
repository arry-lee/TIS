#__author__ = "arry lee"

import cv2
import numpy as np
import prettytable

from awesometable import AwesomeTable, from_str, hstack, table2image, vstack
import faker
f = faker.Faker()


class LayoutTable(AwesomeTable):
    """布局表格"""
    def __init__(self,field_names=None, **kwargs):
        super().__init__(field_names, kwargs=kwargs)
        self.vrules = prettytable.FRAME
        self.hrules = prettytable.NONE
        self._padding_width = 0
        self._left_padding_width = 0
        self._right_padding_width = 0
        self.hide_outlines()

    def hide_outlines(self):
        self._horizontal_char = ""
        self._vertical_char = ""
        self._junction_char = ""
        self._top_junction_char = ""
        self._bottom_junction_char = ""
        self._right_junction_char = ""
        self._left_junction_char = ""
        self._top_right_junction_char = ""
        self._top_left_junction_char = ""
        self._bottom_right_junction_char = ""
        self._bottom_left_junction_char = ""


class HorLayout(object):
    """输入二维列表，输出布局"""
    def __init__(self,layouts = None,widths=None):
        self.layouts = layouts or []
        if isinstance(widths,int):
            self._widths = [widths]*len(self.layouts)
        elif isinstance(widths,list):
            self._widths = widths
        else:
            self._widths = [x.table_width for x in self.layouts]
        self._table_width = sum(x+1 for x in self._widths)-1
        self.table = LayoutTable()

    def add_table(self,table):
        self.layouts.append(table)

    def add_layout(self,layout):
        self.layouts.append(layout)

    @property
    def table_width(self):
        return self._table_width

    @table_width.setter
    def table_width(self,val):
        self._table_width = val

    @property
    def widths(self):
        return self._widths

    @widths.setter
    def widths(self,val):
        self._widths = val

    def __str__(self):
        return self.get_string()

    def get_string(self):
        row = []
        for lot,w in zip(self.layouts,self._widths):
            lot.table_width = w
            row.append(str(lot))
        self.table.clear_rows()
        self.table.add_row(row)
        return self.table.get_string()

    def get_image(self):
        col = []
        for lot, w in zip(self.layouts, self._widths):
            lot.table_width = w
            imgc = lot.get_image()
            if isinstance(imgc,dict):
                col.append(imgc['image'])
            else:
                col.append(imgc)
        # img = np.hstack(col)
        h = max(x.shape[0] for x in col)
        w = sum(x.shape[1] for x in col)
        img = np.ones((h,w,3),np.uint8)*255
        x = 0
        for im in col:
            h,w = im.shape[:2]
            img[0:h,x:x+w] = im
            x+=w
        return img


class VerLayout(object):
    """输入二维列表，输出布局"""
    def __init__(self,layouts = None,widths=None):
        self.layouts = layouts or []
        if isinstance(widths, int):
            self._widths = [widths] * len(self.layouts)
            self._table_width = widths
        elif isinstance(widths, list):
            self._widths = widths
            self._table_width = max(widths)
        else:
            self._table_width = max([x.table_width for x in self.layouts])
            self._widths = [self._table_width]* len(self.layouts)
        self.table = LayoutTable()


    def add_table(self,table):
        self.layouts.append(table)
        # self._widths.append(table.table_width)

    def add_layout(self,layout):
        self.layouts.append(layout)
        # self._widths.append(layout.table_width)

    @property
    def table_width(self):
        return self._table_width

    @table_width.setter
    def table_width(self,val):
        self._table_width = val
        self._widths = [self._table_width] * len(self.layouts)

    def __str__(self):
        return self.get_string()

    def get_string(self):
        row = []
        for lot, w in zip(self.layouts, self._widths):
            lot.table_width = w
            row.append([str(lot)])
        self.table.clear_rows()
        self.table.add_rows(row)
        return self.table.get_string()

    def get_image(self):
        row = []

        for lot, w in zip(self.layouts, self._widths):
            lot.table_width = w
            imgc = lot.get_image()
            if isinstance(imgc, dict):
                row.append(imgc['image'])
            else:
                row.append(imgc)
        h = sum(x.shape[0] for x in row)
        w = max(x.shape[1] for x in row)
        img = np.ones((h,w,3),np.uint8)*255
        y = 0
        for im in row:
            h,w = im.shape[:2]
            img[y:y+h,0:w] = im
            y+=h
        # img = np.vstack(row)
        return img


class TextTable(AwesomeTable):
    """文本框"""
    def __init__(self,string,table_width=None,indent=0):
        super().__init__()
        self.add_row([' '*indent+string])
        self.align = 'l'
        self.table_width = table_width
        self._padding_width = 0
        self._left_padding_width = 0
        self._right_padding_width = 0

    def get_image(self,**kwargs):
        kwargs['vrules'] = 'NONE'
        kwargs['hrules'] = 'NONE'
        kwargs['font_path'] = 'simfang.ttf'
        return super(TextTable, self).get_image(**kwargs)


def from_list(ls,t2b=True,w=None):
    if t2b:
        rows = []
        for value in ls:
            if isinstance(value, list):
                tv = from_list(value, not t2b,w)
            elif isinstance(value, AwesomeTable):
                value.table_width = w
                tv = AwesomeTable()
                tv.add_row([value.get_string()])
            else:
                tv = from_str(value,w+2)

            rows.append(tv)
        return vstack(rows)
    else:
        cols = []
        for value in ls:
            if isinstance(value, list):
                tv = from_list(value, not t2b,w)
            elif isinstance(value, AwesomeTable):
                value.table_width = w
                tv = AwesomeTable()
                tv.add_row([value.get_string()])
            else:
                tv = from_str(value,w+2)
            cols.append(tv)
        return hstack(cols)

if __name__ == '__main__':
    a = TextTable(f.paragraph(10),77)
    strtable = TextTable(f.paragraph(10),indent=0)
    # print(a.table_height)

    nt = AwesomeTable([[1,2,3],[4,5,6],[7,8,9]],title_pos='b',title='table 1')
    strtable2 = TextTable(f.paragraph(10),indent=0)
    strtable3 = TextTable(f.paragraph(10),indent=0)
    v = VerLayout([strtable,nt,strtable2],38)
    v2 = VerLayout([strtable3,nt,strtable],38)

    h = HorLayout([v,v2],[38,38])
    # print(a)
    # print(h)

    xx = VerLayout([HorLayout([TextTable(f.paragraph(10),38),TextTable(f.paragraph(10),38)]),
                    AwesomeTable([[1,2,3],[4,5,6],[7,8,9]]),
                    HorLayout([TextTable(f.paragraph(10),38),TextTable(f.paragraph(10),38)])])
    print(xx)
    img = xx.get_image()
    cv2.imwrite('t.jpg',img)
