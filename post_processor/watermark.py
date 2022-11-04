"""给图片增加水印（污染，签名等）"""
import random

from PIL import Image, ImageDraw, ImageFont

from post_processor.color import reduce_color
from post_processor.deco import as_cv, as_pillow
from post_processor.rotation import rotate_bound


def add_watermark(img, watermark, pos=None, angle=None):
    """
    添加水印效果
    :param img: np.ndarray 原图
    :param watermark: np.ndarray | pathlike | PIL.Image 水印图
    :param pos: tuple[int,int] 坐标
    :param angle: float 旋转角度
    :return: PIL.Image
    """
    img = as_pillow(img)
    width, height = img.size
    if pos is None:
        pos = random.randint(0, 3 * width // 4), random.randint(0, 3 * height // 4)
    if angle is None:
        angle = random.randint(0, 45)

    watermark = as_cv(watermark)
    watermark = rotate_bound(watermark, angle)
    watermark = reduce_color(watermark, 2)
    watermark = as_pillow(watermark)
    mask = watermark.convert("L").point(lambda x: 0 if x > 200 else x)
    img.paste(watermark, pos, mask=mask)
    return img


def signature(text, font_path="static/fonts/shouxie.ttf", size=45):
    """
    生成手写签名图片
    :param text: str 名字
    :param font_path: str 字体路径
    :param size: int 字体大小
    :return: PIL.Image
    """
    font = ImageFont.truetype(font_path, size, encoding="utf-8")
    img = Image.new("RGB", font.getsize(text), "white")
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, fill="black", font=font)
    return img


def add_signature(img, text, pos=None, angle=None):
    """
    添加签名
    :param img: np.ndarray 原图
    :param text: str 文本
    :param pos: tuple[int,int] 位置
    :param angle: float degree 角度
    :return: PIL.Image
    """
    return add_watermark(img, signature(text), pos, angle)
