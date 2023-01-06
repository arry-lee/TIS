"""
本模块保存常用的数据格式转换函数
"""
from functools import wraps

import cv2
import numpy as np
from PIL import Image


def p2c(image):
    """
    The p2c function converts an image from pillow format to cv2 format.

    :param image: Convert the image to a cv2 format
    :return: A cv2 image
    :doc-author: Trelent
    """
    if isinstance(image, np.ndarray):
        return image
    if image.mode == "RGBA":
        return cv2.cvtColor(np.asarray(image, np.uint8), cv2.COLOR_RGBA2BGRA)
    return cv2.cvtColor(np.asarray(image, np.uint8), cv2.COLOR_RGB2BGR)


def c2p(image):
    """
    The c2p function converts an image from the cv2 format to the pillow format.
    The function takes in a single argument, image, which is a numpy array of shape (height, width) or (height, width, 3).
    If the input is only two dimensional it will be converted to grayscale. If there are three dimensions then it will be
    converted to rgb color space.

    :param image: Convert the image from cv2 to pil
    :return: A pil
    :doc-author: Trelent
    """
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


def processor(func):
    """
    将处理器函数包装成可以处理字典的,以及任何输入图像的输入转换
    
    :param func: The function to be decorated
    """
    """
    
    :param func: 被装饰函数
    :return: 装饰器
    """

    @wraps(func)
    def wrap(img, *args, **kwargs):
        if isinstance(img, dict):  # 如果是字典，先尝试处理字典
            try:
                return func(img, *args, **kwargs)
            except:
                pass

            try:
                img["image"] = func(img["image"], *args, **kwargs)  # 然后处理图片
            except:
                if isinstance(img, Image.Image):
                    img["image"] = func(
                        p2c(img["image"]), *args, **kwargs
                    )  # 若类型错误尝试转换类型
                else:
                    img["image"] = func(c2p(img["image"]), *args, **kwargs)
            return img
        
        try:
            return func(img, *args, **kwargs)  # 尝试直接处理图片
        except:
            if isinstance(img, Image.Image):
                return func(p2c(img), *args, **kwargs)  # 若类型错误尝试转换类型
            return func(c2p(img), *args, **kwargs)

    return wrap
