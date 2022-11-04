from pyrect import Rect


def collide_any(rect, others):
    """
    矩形碰撞判断
    :param rect: Rect
    :param others: List[Rect]
    :return: bool
    """
    for other in others:
        if rect.collide(other) or other.collide(rect):
            return True
    return False


def union_all(otherRects):
    left = min([r.left for r in otherRects])
    top = min([r.top for r in otherRects])
    right = max([r.right for r in otherRects])
    bottom = max([r.bottom for r in otherRects])
    return Rect(left, top, right - left, bottom - top)


def max_left(rects):
    """最大剩余矩形
    复杂度 N*4
    """
    rects.append(union_all(rects))
    hlines = set()
    vlines = set()
    for rect in rects:
        hlines.add(rect.top)
        hlines.add(rect.bottom)
        vlines.add(rect.left)
        vlines.add(rect.right)
    vlines = list(vlines)
    vlines.sort()
    hlines = list(hlines)
    hlines.sort()

    rects.pop()
    max_rect = Rect()
    max_area = 0
    for li in range(0, len(vlines) - 1):
        for ri in range(li + 1, len(vlines)):
            for ti in range(0, len(hlines) - 1):
                for bi in range(ti + 1, len(hlines)):
                    c = Rect(
                        vlines[li],
                        hlines[ti],
                        vlines[ri] - vlines[li],
                        hlines[bi] - hlines[ti],
                    )
                    if not collide_any(c, rects) and c.area >= max_area:
                        max_rect = c
                        max_area = c.area
    return max_rect
