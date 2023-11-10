"""
颜色聚类模块，减少图像的杂色
"""

import cv2
import numpy as np

from postprocessor.convert import as_array


def reduce_color(image, num=3):
    """
    通过聚类将图像中的颜色简化为 num 种
    :param image: np.ndarray | path
    :param num: int color numbers
    :return: np.ndarray
    """
    image = as_array(image)
    flat = np.float32(image.reshape((-1, 3)))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, label, center = cv2.kmeans(
        flat, num, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
    )
    # Now convert back into uint8, and make original image
    center = np.uint8(center)
    res = center[label.flatten()]
    res2 = res.reshape((image.shape))
    return res2


def split_color(image):
    """
    提取两个主色，前景色和背景色
    :param image: np.ndarray
    :return: tuple background and foreground
    """
    flat = np.float32(image.reshape((-1, 3)))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, __, center = cv2.kmeans(flat, 2, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    return center[0], center[1]


def mean_color(colors):
    """平均色"""
    flat = np.float32(colors.reshape((-1, 3)))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, __, center = cv2.kmeans(flat, 1, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    return center[0]


def most_color(colors):
    """最多的颜色"""
    return np.mean(colors)


def get_colormap(image):
    """重新着色"""
    image = reduce_color(image, 3)
    cmap = [None] * 256

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    for i in range(h):
        for j in range(w):
            cmap[gray[i, j]] = image[i, j, :]

    last_color = None

    for c in cmap:
        if c is not None:
            last_color = c
            break

    for idx, c in enumerate(cmap):
        if c is None:
            cmap[idx] = last_color
        else:
            last_color = c

    return cmap


def colormap(image, cmap):
    h, w = image.shape
    out = np.zeros((h, w, 3), np.uint8)
    for i in range(h):
        for j in range(w):
            out[i, j] = cmap[image[i, j]]
    return out
