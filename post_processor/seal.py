"""
印章生成相关相关模块
"""
import math
import random

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from post_processor.deco import as_cv, as_pillow, c2p
from post_processor.rotation import rotate_bound


def gen_name_seal(name, font_size=40, yang=True):
    """
    生成人名方章
    :param name: str 人名
    :param font_size: int 字体大小
    :param yang: bool 阴阳
    :return: PIL.Image
    """
    if yang:
        bg_color, fg_color = 'white', 'red'
    else:
        bg_color, fg_color = 'red', 'white'
    font = ImageFont.truetype('simkai.ttf', font_size)
    if len(name) == 3:
        size = (2 * font_size, 2 * font_size)
        width, height = size
        out = Image.new('RGB', size, 'white')
        draw = ImageDraw.Draw(out)
        draw.rounded_rectangle((0, 0) + (width - 1, height - 1), radius=5,
                               fill=bg_color, outline=fg_color,
                               width=2)
        draw.text((0, 0), name[2], fill=fg_color, font=font)
        draw.text((font_size, 0), name[0], fill=fg_color, font=font)
        draw.text((font_size, font_size), name[1], fill=fg_color, font=font)
        draw.text((0, font_size), '印', fill=fg_color, font=font)
    else:
        size = font.getsize(name)
        out = Image.new('RGB', size, 'white')
        draw = ImageDraw.Draw(out)
        width, height = size
        draw.rounded_rectangle((0, 0) + (width - 1, height - 1), radius=4,
                               fill=bg_color,
                               outline=fg_color, width=2)
        draw.text((0, 0), name, fill=fg_color, font=font)
    return out


def gen_seal(text, bottom_text='结算专用章', center_text='2021.01.01', width=200,
             usestar=False):
    """
    圆形印章生成器
    :param text: str 主外圈文字
    :param bottom_text: str 底部文字
    :param center_text: str 中心文字
    :param width: int 图像宽度
    :param usestar: bool 是否使用五角星图案
    :return: np.ndarray
    """
    if usestar:
        out = Image.open('./static/seal/star.png').resize((width, width))
    else:
        out = Image.new('RGB', (width, width), 'white')
    draw = ImageDraw.Draw(out)
    draw.ellipse((0, 0) + (width, width), outline='red', width=5)
    font = ImageFont.truetype('./static/fonts/simfang.TTF', 20,
                              encoding='utf-8')
    font_small = ImageFont.truetype('./static/fonts/simfang.TTF', 16,
                                    encoding='utf-8')
    draw.text((width // 2, width - 30), bottom_text, fill='red',
              font=font_small, anchor='mm', stroke_fill='red', stroke_width=1)
    draw.text((width // 2, width // 2), center_text, fill='red',
              font=font_small, anchor='mm', stroke_fill='red', stroke_width=1)
    lot = len(text)
    deg = 1.5 * math.pi / (lot - 1)
    radius = width // 2 - 25
    center_x, center_y = width // 2, width // 2
    points = [(center_x - radius * math.cos(deg * i - math.pi / 4),
               center_y - radius * math.sin(deg * i - math.pi / 4)) for i in
              range(lot)]
    txts = []
    for i in range(lot):
        txt = Image.new('RGB', (20, 20), 'white')
        draw_txt = ImageDraw.Draw(txt)
        draw_txt.text((10, 10), text[i], fill='red', font=font, anchor='mm',
                      stroke_fill='red', stroke_width=1)
        txt = cv2.cvtColor(np.array(txt), cv2.COLOR_RGB2BGR)
        txt = rotate_bound(txt, 135 - 270 / (lot - 1) * i,
                           border_value=(255, 255, 255))
        txts.append(txt)
    out = cv2.cvtColor(np.array(out), cv2.COLOR_RGB2BGR)
    for pos, txt in zip(points, txts):
        ptx, pty = int(pos[0]), int(pos[1])
        height, width = txt.shape[:2]
        out[pty - height // 2:pty - height // 2 + height,
        ptx - width // 2:ptx + width - width // 2] = txt
    return out


def add_seal(img, seal_p='./static/seal/seal.jpg', pos=None, angle=None):
    """
    给图像添加印章效果
    :param img: 原图
    :param seal_p: 印章
    :param pos: 位置
    :param angle: 角度
    :return: PIL.Image
    """
    img = as_pillow(img)
    width, height = img.size
    if pos is None:
        pos = random.randint(0, 3 * width // 4), random.randint(0,
                                                                3 * height // 4)
    if angle is None:
        angle = random.randint(0, 45)
    seal_p = as_cv(seal_p)
    seal = c2p(rotate_bound(seal_p, angle, border_value=(255, 255, 255)))
    mask = seal.convert('L').point(lambda x: 0 if x > 200 else 200)
    img.paste(seal, pos, mask=mask)
    return img


def add_seal_box(img, seal_p='./static/seal/seal.jpg', pos=None, angle=None,
                 arc_seal=True):
    """
    给图像添加印章效果, 返回图像和印章位置
    :param img: 原图
    :param seal_p: 印章
    :param pos: 位置
    :param angle: 角度
    :param arc_seal: 是否是圆形章
    :return: tuple[PIL.ndarray,tuple[int,int,int,int]]
    """
    img = as_pillow(img)
    width, height = img.size
    if pos is None:
        pos = (random.randint(0, 3 * width // 4),
               random.randint(0, 3 * height // 4))
    if angle is None:
        angle = random.randint(0, 45)
    seal_p = as_cv(seal_p)
    seal = c2p(rotate_bound(seal_p, angle, border_value=(255, 255, 255)))
    mask = seal.convert('L').point(lambda x: 0 if x > 200 else 200)
    img.paste(seal, pos, mask=mask)
    height, width = seal_p.shape[:2]
    if arc_seal:
        x_0, y_0 = pos
        x_0 += (seal.width - width) // 2
        y_0 += (seal.height - height) // 2
        x_1, y_1 = x_0 + width, y_0 + height
    else:
        x_0, y_0 = pos
        x_1, y_1 = x_0 + seal.width, y_0 + seal.height
    return img, (x_0, y_0, x_1, y_1)
