"""
裂痕效果
"""
import random

from PIL import Image

from postprocessor.convert import as_image

THICKNESS = 5


def _random_tear_curve(width, slope=0):
    """
    生成固定宽度的撕裂线，一条折线，但是首尾偏移量为 slope*width
    :param width: 图片宽度
    :param slope: 裂痕斜率 [-0.5,0.5]
    :return: list
    """
    if not -0.5 <= slope <= 0.5:
        raise ValueError("-0.5<= slope <= 0.5")
    offset = int(width * slope)
    ones = offset // 2 + width // 3
    none = -offset // 2 + width // 3  # >0
    zeros = [0] * width
    zeros[:ones] = [1] * ones
    zeros[ones : ones + none] = [-1] * none
    random.shuffle(zeros)
    return zeros


def _random_tear_image(width, height, slope=0):
    """
    生成固定大小的撕裂线图片
    :param width: int 宽度
    :param height: height 高度
    :param slope: 斜率 [-0.5,0.5]
    :return: np.ndarray
    """
    mid = height // 2
    img = Image.new("RGB", (width, height), "black")
    zeros = _random_tear_curve(width, slope)
    for i in range(width):
        mid = mid + zeros[i]
        for j in range(mid):
            img.putpixel((i, j), (200, 200, 200))
        for j in range(mid, mid + THICKNESS):
            img.putpixel((i, j), (255, 255, 255))
        img.putpixel((i, mid), (100, 100, 100))
    return img


def tear_image(img, pos, gap=20, slope=0):
    """
    做出一张图片撕裂后的效果
    :param img: np.ndarray 原图
    :param pos: int 位置
    :param gap: int 裂开宽度
    :param slope: float 斜率
    :return: np.ndarray 裂开图
    """
    img = as_image(img)
    zeros = _random_tear_curve(img.width, slope)
    out = Image.new("RGB", (img.width, img.height + gap), "black")
    mid = pos
    for i in range(img.width):
        mid = mid + zeros[i]
        for j in range(mid):
            out.putpixel((i, j), img.getpixel((i, j)))

        for j in range(mid, mid + THICKNESS):
            img.putpixel((i, j), (255, 255, 255))
        img.putpixel((i, mid), (100, 100, 100))
        for j in range(mid, img.height):
            out.putpixel((i, j + gap), img.getpixel((i, j)))
    return out


def tear_image_alpha(img, pos, gap=20, slope=0):
    """
    做出一张图片撕裂后的效果
    :param img: np.ndarray 原图
    :param pos: int 位置
    :param gap: int 裂开宽度
    :param slope: float 斜率
    :return: np.ndarray 裂开图
    """
    img = as_image(img).convert("RGBA")
    zeros = _random_tear_curve(img.width, slope)
    out = Image.new("RGBA", (img.width, img.height + gap), (0, 0, 0, 0))
    mid = pos
    for i in range(img.width):
        mid = mid + zeros[i]
        for j in range(mid):
            out.putpixel((i, j), img.getpixel((i, j)))

        for j in range(mid, mid + THICKNESS):
            out.putpixel((i, j), (255, 255, 255, 255))
        out.putpixel((i, mid), (100, 100, 100, 255))

    return out
