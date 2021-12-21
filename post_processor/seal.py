import math
import random
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont

from post_processor.deco import as_pillow, c2p
from post_processor.rotation import rotate_bound


def gen_seal(text, bottom_text='结算专用章', center_text='2021.01.01', width=200):
    """印章生成器"""
    out = Image.new('RGB', (width, width), 'white')
    draw = ImageDraw.Draw(out)
    draw.ellipse((0, 0) + (width, width), outline='red', width=5)

    font = ImageFont.truetype('./static/fonts/simfang.TTF', 20, encoding='utf-8')
    font_small = ImageFont.truetype('./static/fonts/simfang.TTF', 16, encoding='utf-8')
    draw.text((width // 2, width - 30), bottom_text, fill='red',
              font=font_small, anchor='mm',stroke_fill='red',stroke_width=1)
    draw.text((width // 2, width // 2), center_text, fill='red',
              font=font_small, anchor='mm',stroke_fill='red',stroke_width=1)

    lot = len(text)
    deg = 1.5 * math.pi / (lot - 1)
    r = width // 2 - 25
    cx, cy = width // 2, width // 2
    points = [(cx - r * math.cos(deg * i - math.pi / 4),
               cy - r * math.sin(deg * i - math.pi / 4)) for i in range(lot)]
    txts = []
    for i in range(lot):
        txt = Image.new('RGB', (20, 20), 'white')
        draw_txt = ImageDraw.Draw(txt)
        draw_txt.text((10, 10), text[i], fill='red', font=font, anchor='mm',stroke_fill='red',stroke_width=1)
        txt = cv2.cvtColor(np.array(txt), cv2.COLOR_RGB2BGR)
        txt = rotate_bound(txt, 135 - 270 / (lot - 1) * i,borderValue=(255,255,255))
        txts.append(txt)

    out = cv2.cvtColor(np.array(out), cv2.COLOR_RGB2BGR)
    for pos, txt in zip(points, txts):
        x, y = int(pos[0]), int(pos[1])
        h, w = txt.shape[:2]
        out[y - h // 2:y - h // 2 + h, x - w // 2:x + w - w // 2] = txt
    return out


def add_seal(img, seal_p='./static/seal/seal.jpg', xy=None, angle=None):
    """ 添加印章效果

    img：原图
    xy: 位置
    angle: 角度
    seal: 文件或印章图
    """
    # imageit(img)
    img = as_pillow(img)
    w, h = img.size

    if xy is None:
        xy = random.randint(0, 3 * w // 4), random.randint(0, 3 * h // 4)
    if angle is None:
        angle = random.randint(0, 45)

    seal = c2p(rotate_bound(cv2.imread(seal_p, cv2.IMREAD_COLOR), angle,borderValue=(255,255,255)))
    mask = seal.convert('L').point(lambda x: 0 if x > 200 else 255)
    img.paste(seal, xy, mask=mask)
    return img