import cv2
import numpy as np
from PIL import Image, ImageDraw

from postprocessor.deco import c2p, p2c


def poison_text(image, xy, text, fill, font, anchor="lt", mode="mixed"):
    """
    使用泊松编辑在背景上写字
    :param image: 背景图片 IMAGE
    :param xy: 位置 (x,y)
    :param text: 文本 str
    :param fill: 颜色 (0,0,0)
    :param font: 字体 ImageFont
    :param anchor: 锚点 'lt'
    :param mode: 方法 mixed 泊松编辑，normal 普通融合
    :return: Image 融合后的图片
    """
    if image.mode == "RGBA":
        image = image.convert("RGB")
    obj = Image.new("RGB", image.size, (255, 255, 255))
    obj_draw = ImageDraw.Draw(obj)
    mask = Image.new("L", image.size, 0)
    mask_draw = ImageDraw.Draw(mask)

    obj_draw.text(xy, text, fill, font, anchor)
    mask_draw.text(xy, text, 255, font, anchor, stroke_width=6, stroke_fill=255)
    box = mask_draw.textbbox(xy, text, font, anchor, stroke_width=6)

    # x,y = xy
    center = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2

    obj_img = p2c(obj.crop(box))
    mask_img = np.asarray(mask.crop(box), np.uint8)
    if mode == "mixed":
        mode = cv2.MIXED_CLONE
    elif mode == "normal":
        mode = cv2.NORMAL_CLONE
    else:
        mode = cv2.MONOCHROME_TRANSFER
    try:
        res = cv2.seamlessClone(obj_img, p2c(image), mask_img, center, mode)
    except cv2.error:
        print(text)
        return image
    return c2p(res)


# font = ImageFont.truetype('simfang.ttf', 40)
# bg = Image.open(r"E:\00IT\P\uniform\multilang\output_data\idcard\ms_MY\idcard_ms_MY_00000000_1665297329.png")
# res = poison_text(bg, (500, 600), 'Iloveyou', (255, 0, 0), font)
# res = poison_text(res, (500, 800), 'Iloveyou', (255, 0, 0), font)
#
# res.show()
