import numpy as np

from post_processor.deco import as_pillow, p2c


def add_background(image,background,offset=0,mask=None):
    img = as_pillow(image)
    h, w = image.shape[:2]
    h += offset*2
    w += offset*2
    bg = as_pillow(background).resize((w,h))
    # mask = img.convert('L').point(lambda x: 0 if x < 10 else 255)
    print(mask)
    if mask is not None:
        mask = as_pillow(mask).convert('L')
    bg.paste(img,(offset,offset),mask=mask)
    return p2c(bg)


def add_background_data(data,background,offset):
    assert isinstance(data,dict)
    mask = data.get('mask',None)
    data['image'] = add_background(data['image'],background,offset,mask=mask)
    data['points'] =  np.array(data['points']) + offset
    return data