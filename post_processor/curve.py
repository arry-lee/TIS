"""
随机曲线生成模块
"""
import random
from io import BytesIO

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from bezier import curve as _curve
from post_processor.scan import spread


def bezier_curve(points, color="red"):
    """
    生成曲线图片
    :param points: list 控制点列表
    :param color: str 曲线颜色
    :return: np.ndarray 曲线图片
    """
    t_points = np.arange(0, 1, 0.01)
    points = np.array(points)
    curve1 = _curve(t_points, points)
    plt.rcParams["figure.figsize"] = (4.0, 1.0)
    plt.rcParams["savefig.dpi"] = 300
    plt.rcParams["figure.dpi"] = 300
    plt.figure()
    plt.plot(
        curve1[:, 0], curve1[:, 1], color=color  # x-coordinates.  # y-coordinates.
    )

    buffer = BytesIO()
    plt.axis("off")  # 隐藏x坐标轴
    plt.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0)
    new_img = np.asarray(Image.open(buffer))  # new_img就是figure的数组
    plt.close()
    buffer.close()
    return cv2.cvtColor(new_img, cv2.COLOR_RGB2BGR)


def random_curve(num=5, high=4):
    """
    随机曲线
    :param num: int 控制点数量
    :param high: int 控制点坐标最大值
    :return: np.ndarray 随机曲线图
    """
    pts = np.random.randint(0, high, (num, 2), np.int32)
    color = random.choice(["red", "green", "blue", "black", "yellow"])
    return bezier_curve(pts, color)


def random_ink():
    """随机笔迹"""
    img = random_curve()
    return cv2.blur(spread(img), ksize=(3, 3))
