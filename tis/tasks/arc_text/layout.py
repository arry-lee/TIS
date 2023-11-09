# __author__ = "arry lee"
# 2022-2-21 17:37:31
# LayoutTable 用于管理布局


from abc import ABCMeta, abstractmethod
from PIL import Image


class AbstractTable(object, metaclass=ABCMeta):
    def __init__(self):
        self.layouts = []

    def __str__(self):
        return self.get_string()

    @abstractmethod
    def get_string(self):
        return NotImplemented

    @property
    def height(self):
        return self.get_image()["image"].height

    @abstractmethod
    def get_image(self):
        return NotImplemented

    def append(self, obj):
        if hasattr(obj, "get_image"):
            self.layouts.append(obj)
        else:
            raise ValueError("Not Layout or Table")


class HorLayout(AbstractTable):
    """水平方向布局的抽象
    任何实现了 get_image 方法和 table_width 属性的类表格，
    均可作为布局管理的 layouts列表的子元素，包括布局自身
    """

    def __init__(self, layouts=None, widths=None, gaps=None):
        super().__init__()
        self.layouts = layouts or []

        if isinstance(widths, int):
            self._widths = [widths] * len(self.layouts)
        elif isinstance(widths, list):
            self._widths = widths
        else:
            self._widths = [x.table_width for x in self.layouts]

        if isinstance(gaps, int):
            self._gaps = [gaps] * (len(self.layouts) - 1)
        elif isinstance(gaps, list):
            self._gaps = gaps
        else:
            self._gaps = [0] * (len(self.layouts) - 1)
        # _char_width 是字符属性 _table 是图像属性
        self._char_width = sum(x + 1 for x in self._widths) - 1
        self._table_width = sum(self._widths) + sum(self._gaps)

    @property
    def table_width(self):
        return self._table_width

    @table_width.setter
    def table_width(self, val):
        self._table_width = val

    @property
    def widths(self):
        return self._widths

    @widths.setter
    def widths(self, val):
        self._widths = val

    def get_image(self):
        col = []
        out = {}
        for lot, w in zip(self.layouts, self._widths):
            lot.table_width = w
            imgc = lot.get_image()
            col.append(imgc)
        # 计算背景尺寸
        h = max(x["image"].height for x in col)
        w = sum(x["image"].width for x in col) + sum(self._gaps)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        x = 0
        y = 0
        gaps = self._gaps + [0]
        for data, gap in zip(col, gaps):
            w, h = data["image"].size
            img.paste(data["image"], (x, y) + (x + w, y + h), data["image"])

            # data.points is list[np]
            ps = data["points"]
            n = []
            for p in ps:
                n.append(p + (x, y))
            data["points"] = n

            if not out:
                out = data
            else:
                out["image"] = img
                out["label"].extend(data["label"])
                out["points"].extend(data["points"])
            x += w + gap
        return out


class VerLayout(AbstractTable):
    """输入二维列表，输出布局"""

    def __init__(self, layouts=None, widths=None, gaps=None):
        super().__init__()
        self.layouts = layouts or []
        if isinstance(widths, int):
            self._widths = [widths] * len(self.layouts)
            self._table_width = widths
        elif isinstance(widths, list):
            self._widths = widths
            self._table_width = max(widths)
        else:
            self._table_width = max([x.table_width for x in self.layouts])
            self._widths = [self._table_width] * len(self.layouts)

        if isinstance(gaps, int):
            self._gaps = [gaps] * (len(self.layouts) - 1)
        elif isinstance(gaps, list):
            self._gaps = gaps
        else:
            self._gaps = [0] * (len(self.layouts) - 1)

    @property
    def table_width(self):
        return self._table_width

    @table_width.setter
    def table_width(self, val):
        self._table_width = val
        self._widths = [self._table_width] * len(self.layouts)

    def get_image(self):
        row = []
        out = {}
        for lot, w in zip(self.layouts, self._widths):
            lot.table_width = w
            imgc = lot.get_image()
            row.append(imgc)

        h = sum(x["image"].height for x in row) + sum(self._gaps)
        w = max(x["image"].width for x in row)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        x = 0
        y = 0
        gaps = self._gaps + [0]
        for data, gap in zip(row, gaps):
            w, h = data["image"].size
            img.paste(data["image"], (x, y) + (x + w, y + h), data["image"])
            ps = data["points"]
            n = []
            for p in ps:
                n.append(p + (x, y))
            data["points"] = n
            if not out:
                out = data
            else:
                out["image"] = img
                out["label"].extend(data["label"])
                out["points"].extend(data["points"])
            y += h + gap
        return out
