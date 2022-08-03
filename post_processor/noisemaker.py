"""
图像噪声生成模块
"""
import random

import numpy as np


def sp_noise(image, prob=0.01):
    """
    添加椒盐噪声
    :param image: np.ndarray
    :param prob: 噪声比例
    :return: np.ndarray
    """
    output = np.zeros(image.shape, np.uint8)
    thres = 1 - prob
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            rdn = random.random()
            if rdn < prob:
                output[i][j] = 0
            elif rdn > thres:
                output[i][j] = 255
            else:
                output[i][j] = image[i][j]
    return output


def gauss_noise(image, mean=0, var=0.001):
    """
    添加高斯噪声
    :param image: np.ndarray
    :param mean: 均值
    :param var: 方差
    :return: np.ndarray
    """
    image = np.array(image / 255, dtype=float)
    noise = np.random.normal(mean, var**0.5, image.shape)
    out = image + noise
    if out.min() < 0:
        low_clip = -1.0
    else:
        low_clip = 0.0
    out = np.clip(out, low_clip, 1.0)
    out = np.uint8(out * 255)
    return out
