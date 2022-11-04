from collections import defaultdict


class TextBox(object):
    """文字框"""

    def __init__(self, x1, y1, x2, y2, text, direction="ltr"):
        self.left = x1
        self.right = x2
        self.top = y1
        self.bottom = y2
        self.text = text
        self.direction = direction

    def __repr__(self):
        return "<TextBox %d %d %d %d %s %s>" % (
            self.left,
            self.top,
            self.right,
            self.bottom,
            self.text,
            self.direction,
        )

    def __str__(self):
        return "%d;%d;%d;%d;@%s" % (
            self.left,
            self.top,
            self.right,
            self.bottom,
            self.text,
        )

    @property
    def box(self):
        return self.left, self.top, self.right, self.bottom

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def width(self):
        return self.right - self.left

    def check_direction(self):
        # 检测文字旋转方向
        if (
            self.text.isascii()
            and self.text.startswith("0")
            and self.direction == "t2b"
        ):
            self.text = "".join(reversed([x for x in self.text]))
            self.direction = "b2t"

    def shrink(self, ratio=0.9):
        # 纯数字母的时候给字高框缩水
        if self.text.isascii():
            if self.direction == "ltr":
                delta = int(ratio * self.height)
                self.top += delta
                self.bottom -= delta
            else:
                delta = int(ratio * self.width)
                self.left += delta
                self.right -= delta


def hgroup(tblist):
    """将文本框进行重组"""
    d = defaultdict(list)
    for tbox in tblist:
        d[tbox.top].append(tbox)
    out = []
    # 横向连接的框
    singlelist = []
    for k in d:
        d[k].sort(key=lambda x: x.left, reverse=True)
        stack = []
        while d[k]:
            other = d[k].pop()
            if not stack:
                stack.append(other)
                continue

            self = stack[-1]
            if (
                self.right == other.left
                and self.top == other.top
                and self.bottom == other.bottom
            ):
                stack.append(other)
            else:
                if len(stack) == 1:
                    # out.append(stack[0])
                    singlelist.append(stack[0])
                elif len(stack) > 1:
                    newbox = stack[0]
                    newbox.right = stack[-1].right
                    newbox.text = "".join([x.text for x in stack])
                    out.append(newbox)
                stack = [other]

        if len(stack) == 1:
            # out.append(stack[0])
            singlelist.append(stack[0])
        elif len(stack) > 1:
            newbox = stack[0]
            newbox.right = stack[-1].right
            newbox.text = "".join([x.text for x in stack])
            out.append(newbox)

    return out, singlelist


def vgroup(tblist):
    """将文本框进行重组"""
    d = defaultdict(list)
    for tbox in tblist:
        d[tbox.left].append(tbox)
    out = []
    # 横向连接的框
    singlelist = []
    for k in d:
        d[k].sort(key=lambda x: x.top, reverse=True)
        stack = []
        while d[k]:
            other = d[k].pop()
            if not stack:
                stack.append(other)
                continue

            self = stack[-1]
            if (
                self.bottom == other.top
                and self.left == other.left
                and self.right == other.right
            ):
                stack.append(other)
            else:
                if len(stack) == 1:
                    # out.append(stack[0])
                    singlelist.append(stack[0])
                elif len(stack) > 1:
                    newbox = stack[0]
                    newbox.bottom = stack[-1].bottom
                    newbox.text = "".join([x.text for x in stack])
                    newbox.direction = "t2b"
                    out.append(newbox)
                stack = [other]

        if len(stack) == 1:
            # out.append(stack[0])
            singlelist.append(stack[0])
        elif len(stack) > 1:
            newbox = stack[0]
            newbox.bottom = stack[-1].bottom
            newbox.text = "".join([x.text for x in stack])
            newbox.direction = "t2b"
            out.append(newbox)

    return out, singlelist


def group(tblist):
    hlist, slist = hgroup(tblist)
    vlist, slist = vgroup(slist)
    return hlist + vlist + slist


if __name__ == "__main__":
    # testlist = [TextBox(0, 0, 5, 5, 'a'),TextBox(5, 20, 10, 25, 'b'), TextBox(5, 25, 10, 30, 'v'), TextBox(5, 0, 10, 5, 'b'),
    #             TextBox(10, 0, 15, 5, 'c'),
    #             TextBox(0, 10, 5, 15, 'a'), TextBox(5, 10, 10, 15, 'b'),
    #             TextBox(10, 10, 15, 15, 'c')]
    #
    # d = group(testlist)
    # print(d)
    print("001".isascii())
