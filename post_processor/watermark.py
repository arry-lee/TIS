# 给图片增加水印（污染，签名等）
import random
from PIL import Image,ImageDraw,ImageFont
from post_processor.deco import as_pillow,as_cv
from post_processor.color_reducer import minimize_color
from post_processor.rotation import rotate_bound


def add_watermark(img, watermark, xy=None, angle=None):
    """ 添加水印效果
    img：原图,路径或 np.ndarray
    watermark: 需要添加的水印
    xy: 位置
    angle: 角度
    """
    img = as_pillow(img)
    w, h = img.size
    if xy is None:
        xy = random.randint(0,  3 * w // 4), random.randint(0,  3 * h // 4)
    if angle is None:
        angle = random.randint(0, 45)

    watermark = as_cv(watermark)
    watermark = rotate_bound(watermark, angle)
    watermark = minimize_color(watermark, 2)
    watermark = as_pillow(watermark)
    mask = watermark.convert('L').point(lambda x: 0 if x > 200 else x)
    img.paste(watermark, xy, mask=mask)
    return img


def signature(text,font='static/fonts/shouxie.ttf',size=45):
    ft = ImageFont.truetype(font, size, encoding='utf-8')
    bg = Image.new('RGB', ft.getsize(text), 'white')
    draw = ImageDraw.Draw(bg)
    draw.text((0, 0), text, fill='black', font=ft)
    return bg

def add_signature(img,text,xy=None, angle=None):
    return add_watermark(img,signature(text),xy,angle)
