"""
颜色聚类模块，减少图像的杂色
"""
import cv2 as cv
import numpy as np

from post_processor.deco import as_cv


def reduce_color(img, num=3):
    """
    通过聚类将图像中的颜色简化为 num 种
    :param img: np.ndarray | path
    :param num: int color numbers
    :return: np.ndarray
    """
    img = as_cv(img)
    flat = np.float32(img.reshape((-1, 3)))
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, label, center = cv.kmeans(flat, num, None, criteria, 10, cv.KMEANS_RANDOM_CENTERS)
    # Now convert back into uint8, and make original image
    center = np.uint8(center)
    res = center[label.flatten()]
    res2 = res.reshape((img.shape))
    return res2


def split_color(img):
    """
    提取两个主色，前景色和背景色
    :param img: np.ndarray
    :return: tuple background and foreground
    """
    flat = np.float32(img.reshape((-1, 3)))
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, __, center = cv.kmeans(flat, 2, None, criteria, 10, cv.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    return center[0], center[1]
