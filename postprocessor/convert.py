"""
本模块保存常用的数据格式转换函数
"""
import cv2
import numpy as np
from PIL import Image


def p2c(image):
    """
    convert image format from pillow to cv
    :param image: PIL.Image
    :return: cv2.image
    """
    if isinstance(image, np.ndarray):
        return image
    if image.mode == "RGBA":
        return cv2.cvtColor(np.asarray(image, np.uint8), cv2.COLOR_RGBA2BGRA)
    return cv2.cvtColor(np.asarray(image, np.uint8), cv2.COLOR_RGB2BGR)


def c2p(image):
    """
    convert image format from cv to pillow
    :param image: cv2.image
    :return: PIL.Image
    """
    if len(image.shape) == 2:
        return Image.fromarray(image, mode="L")
    if image.shape[2] == 3:
        return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA))


def as_image(img):
    """
    convert everything to PIL.Image
    :param img: path/np.ndarray/PIL.Image
    :return: PIL.Image
    """
    if isinstance(img, str):
        return Image.open(img)
    if isinstance(img, np.ndarray):
        return c2p(img)
    return img


def as_array(img):
    """
    convert everything to np.ndarray
    :param img: path/np.ndarray/PIL.Image
    :return: np.ndarray
    """
    if isinstance(img, str):
        return cv2.imread(img, cv2.IMREAD_UNCHANGED)
    if isinstance(img, Image.Image):
        return p2c(img)
    return img


def keepdata(func):
    """
    将处理器函数包装成可以处理字典的,任何输入图像的输入转换为cv,输出为cv
    :param func: 被装饰函数
    :return: 装饰器
    """

    def wrap(img, *args, **kwargs):
        if isinstance(img, str):
            oimg = cv2.imread(img, cv2.IMREAD_COLOR)
        elif isinstance(img, Image.Image):
            oimg = p2c(img)
        elif isinstance(img, dict):
            oimg = as_array(img["image"])

        else:
            oimg = img

        res = func(oimg, *args, **kwargs)

        if isinstance(img, dict):
            if isinstance(res, Image.Image):
                img["image"] = p2c(res)
            else:
                img["image"] = res
        else:
            if isinstance(res, Image.Image):
                img["image"] = p2c(res)
            else:
                img["image"] = res
        return img

    return wrap