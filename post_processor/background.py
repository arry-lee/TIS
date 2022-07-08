import numpy as np

from post_processor.deco import as_pillow, c2p, p2c


def add_background(image, background, offset=0, mask=None):
    img = as_pillow(image)
    h, w = image.shape[:2]
    h += offset * 2
    w += offset * 2
    bg = as_pillow(background).resize((w, h))
    # mask = img.convert('L').point(lambda x: 0 if x < 10 else 255)
    # print(mask)
    if mask is not None:
        mask = as_pillow(mask).convert('L')
    bg.paste(img, (offset, offset), mask=mask)
    return p2c(bg)


def modify_text(text, xy):
    x0, y0 = xy
    x1, y1, x2, y2 = text.box
    x3, y3 = text.xy
    text.box = x1 + x0, y1 + y0, x2 + x0, y2 + y0
    text.xy = x3 + x0, y3 + y0


def modify_line(line, xy):
    x0, y0 = xy
    x1, y1 = line.start
    x2, y2 = line.end
    line.start = x1 + x0, y1 + y0
    line.end = x2 + x0, y2 + y0


def add_background_data(data, background, offset):
    assert isinstance(data, dict)
    mask = data.get('mask', None)
    data['image'] = add_background(data['image'], background, offset, mask=mask)
    data['points'] = np.array(data['points']) + offset
    for t in data['text']:
        modify_text(t,(offset,offset))
    for t in data['line']:
        modify_line(t,(offset,offset))
    return data


def add_to_paper(data, paper):
    bg = paper.image.copy()
    xy = paper.pad[0], paper.pad[1]
    bg.paste(c2p(data['image']), xy)
    data['image'] = p2c(bg)
    data['points'] = np.array(data['points']) + np.array(xy)
    for t in data['text']:
        modify_text(t,xy)
    for t in data['line']:
        modify_line(t,xy)
    return data
