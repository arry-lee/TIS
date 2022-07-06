import cv2
import numpy as np
from PIL import Image


def p2c(image):
    # pillow to cv
    return cv2.cvtColor(np.asarray(image, np.uint8), cv2.COLOR_RGB2BGR)


def c2p(image):
    # cv to pillow
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))


def as_pillow(img):
    if isinstance(img, str):
        return Image.open(img)
    elif isinstance(img, np.ndarray):
        return c2p(img)
    else:
        return img


def as_cv(img):
    if isinstance(img, str):
        return cv2.imread(img, cv2.IMREAD_COLOR)
    elif isinstance(img, Image.Image):
        return p2c(img)
    return img


def imageit(func):
    """将输入图片包装成cv格式"""

    def wrap(img, *args, **kwargs):
        res = func(as_cv(img), *args, **kwargs)
        return res

    return wrap


def keepdata(func):
    """将处理器函数包装成可以处理字典的,
    任何输入图像的输入转换为cv,输出为cv
    """

    def wrap(img, *args, **kwargs):
        if isinstance(img, str):
            oimg = cv2.imread(img, cv2.IMREAD_COLOR)
        elif isinstance(img, Image.Image):
            oimg = p2c(img)
        elif isinstance(img, dict):
            oimg = img["image"]
        else:
            oimg = img

        res = func(oimg, *args, **kwargs)

        if isinstance(img, dict):
            if isinstance(res, Image.Image):
                img["image"] = p2c(res)
            else:
                img["image"] = res
            return img
        else:
            if isinstance(res, Image.Image):
                img["image"] = p2c(res)
            else:
                img["image"] = res

    return wrap
