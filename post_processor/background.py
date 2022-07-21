"""
添加背景
"""
import numpy as np

from post_processor.deco import as_pillow, c2p, p2c


def add_background(image, background, offset=0, mask=None):
    """
    添加背景
    :param image: 原图
    :param background: 背景图
    :param offset: 偏移量
    :param mask: 蒙版
    :return: np.ndarray
    """
    img = as_pillow(image)
    height, width = image.shape[:2]
    height += offset * 2
    width += offset * 2
    back = as_pillow(background).resize((width, height))
    if mask is not None:
        mask = as_pillow(mask).convert('L')
    back.paste(img, (offset, offset), mask=mask)
    return p2c(back)


def _modify_text(text, offsets):
    x_0, y_0 = offsets
    x_1, y_1, x_2, y_2 = text.box
    x_3, y_3 = text.xy
    text.box = x_1 + x_0, y_1 + y_0, x_2 + x_0, y_2 + y_0
    text.xy = x_3 + x_0, y_3 + y_0


def _modify_line(line, offsets):
    x_0, y_0 = offsets
    x_1, y_1 = line.start
    x_2, y_2 = line.end
    line.start = x_1 + x_0, y_1 + y_0
    line.end = x_2 + x_0, y_2 + y_0


def add_background_data(data, background, offset):
    """
    添加背景同时修改标注
    :param data: dict 标注字典
    :param background: 背景图
    :param offset: 偏移量
    :return: dict 新标注字典
    """
    assert isinstance(data, dict)
    mask = data.get('mask', None)
    data['image'] = add_background(data['image'], background, offset, mask=mask)
    data['points'] = np.array(data['points']) + offset
    for text in data['text']:
        _modify_text(text, (offset, offset))
    for line in data['line']:
        _modify_line(line, (offset, offset))
    return data


def add_to_paper(data, paper):
    """
    添加到纸张上
    :param data: dict 标注字典
    :param paper: Paper
    :return: dict 新标注字典
    """
    img = paper.image.copy()
    pos = paper.pad[0], paper.pad[1]
    img.paste(c2p(data['image']), pos)
    data['image'] = p2c(img)
    data['points'] = np.array(data['points']) + np.array(pos)
    for text in data['text']:
        _modify_text(text, pos)
    for line in data['line']:
        _modify_line(line, pos)
    return data
