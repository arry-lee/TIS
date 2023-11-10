"""
随机曲线生成模块
"""
from io import BytesIO

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from postprocessor.bezier import curve as _curve


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
