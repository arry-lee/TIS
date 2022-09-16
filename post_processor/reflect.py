"""
玻璃反光效果

选取一些带有光照效果的图片，作为蒙版按照一定的透明度添加
"""

import cv2
import numpy as np

from post_processor.deco import as_cv


# Photoshop 色阶调整算法
def levelAdjust(img, Sin=0, Hin=255, Mt=1.0, Sout=0, Hout=255):
    Sin = min(max(Sin, 0), Hin - 2)  # Sin, 黑场阈值, 0<=Sin<Hin
    Hin = min(Hin, 255)  # Hin, 白场阈值, Sin<Hin<=255
    Mt = min(max(Mt, 0.01), 9.99)  # Mt, 灰场调节值, 0.01~9.99
    Sout = min(max(Sout, 0), Hout - 2)  # Sout, 输出黑场阈值, 0<=Sout<Hout
    Hout = min(Hout, 255)  # Hout, 输出白场阈值, Sout<Hout<=255

    dif_in = Hin - Sin
    dif_out = Hout - Sout
    table = np.zeros(256, np.uint16)
    for i in range(256):
        v1 = min(max(255 * (i - Sin) / dif_in, 0), 255)  # 输入动态线性拉伸
        v2 = 255 * np.power(v1 / 255, 1 / Mt)  # 灰场伽马调节
        table[i] = min(max(Sout + dif_out * v2 / 255, 0), 255)  # 输出线性拉伸

    out = cv2.LUT(img, table)
    return out


def apply(bottom_img, top_img, func):
    """
    在img1和img2上运用叠加算法，img2在img1 的上层
    :param bottom_img:底层图
    :param top_img:上层图
    :param func:所用算法
    :return:
    """
    if isinstance(func, str):
        if func == "screen":
            func = screen
        elif func == "soft":
            func = soft_lighten
        elif func == "strong":
            func = strong_lighten
        else:
            func = add_color

    bottom_img = as_cv(bottom_img)
    top_img = as_cv(top_img)
    top_img = cv2.resize(top_img, (bottom_img.shape[1], bottom_img.shape[0]))
    img_up = cv2.cvtColor(bottom_img, cv2.COLOR_RGB2BGR, cv2.CV_32FC3)
    img_down = cv2.cvtColor(top_img, cv2.COLOR_RGB2BGR, cv2.CV_32FC3)
    img_up = img_up / 255
    img_down = img_down / 255
    return func(img_up, img_down) * 255


def screen(img1, img2):
    """
    滤色模式
    """
    dst = 1 - (1 - img1) * (1 - img2)
    return dst


def add_color(img1, img2):
    """叠加模式"""
    dst = np.where(img2 > 0.5, 2 * img1 * img2, 1 - 2 * (1 - img1) * (1 - img2))
    return dst


def soft_lighten(img1, img2):
    """柔化模式"""
    dst = np.where(
        img1 <= 0.5,
        (2 * img1 - 1) * (img2 - img2 * img2) + img2,
        (2 * img1 - 1) * (np.sqrt(img2) - img2) + img2,
    )
    return dst


def strong_lighten(img1, img2):
    """强光模式"""
    dst = np.where(img1 <= 0.5, 2 * img1 * img2, 1 - 2 * (1 - img1) * (1 - img2))
    return dst


def reflect(img, light="test.jpeg", ksize=(50, 50), func="screen", alpha=0.3):
    """
    模拟玻璃反射
    https://jingyan.baidu.com/article/4e5b3e193865e8d0911e2444.html
    :return:
    """

    light = as_cv(light)
    out = cv2.blur(light, ksize)
    img2 = levelAdjust(out, 90, 225, 1.0, 10, 245)
    cv2.imwrite("t2.jpg", img2)
    img2 = np.uint8(img2 * alpha)
    out = apply(img, img2, func)
    return out


if __name__ == "__main__":
    for f in ("screen", "soft", "strong", "add"):
        out = reflect(r"E:\00IT\P\uniform\t2.jpg", func=f)
        cv2.imwrite(f"{f}.jpg", out)
