"""给图片增加渐变和光影"""

import cv2
import numpy as np

from postprocessor.convert import as_array

def grad(size, direct, color_start, color_end):
    """
    创建一个渐变蒙版
    :param size: tuple(int,int) 图片大小
    :param direct: str 方向 h为横向 v为纵向
    :param color_start: tuple(int,int,int) 起点颜色
    :param color_end: tuple(int,int,int) 终点颜色
    :return: np.ndarray
    """
    width, height = size
    # 创建一幅与原图片一样大小的透明图片
    grad_img = np.ndarray((height, width, 3), dtype=np.uint8)

    if direct == "h":
        g_b = float(color_end[0] - color_start[0]) / width
        g_g = float(color_end[1] - color_start[1]) / width
        g_r = float(color_end[2] - color_start[2]) / width
        for i in range(height):
            for j in range(width):
                grad_img[i, j, 0] = color_start[0] + j * g_b
                grad_img[i, j, 1] = color_start[1] + j * g_g
                grad_img[i, j, 2] = color_start[2] + j * g_r
    else:
        g_b = float(color_end[0] - color_start[0]) / height
        g_g = float(color_end[1] - color_start[1]) / height
        g_r = float(color_end[2] - color_start[2]) / height
        for i in range(height):
            for j in range(width):
                grad_img[i, j, 0] = color_start[0] + i * g_b
                grad_img[i, j, 1] = color_start[1] + i * g_g
                grad_img[i, j, 2] = color_start[2] + i * g_r

    return grad_img


def add_fold(img, pos, direction="h"):
    """
    加一条折痕的效果
    :param img: np.ndarray
    :param pos: int 位置
    :param direction: str 方向 h 横向 or v 纵向
    :return: np.ndarray
    """
    height, width = img.shape[:2]
    if direction == "h":
        left = img[:, :pos]
        right = img[:, pos:]

        left_light = np.uint8(np.clip((0.8 * left + 1), 0, 255))
        right_light = np.uint8(np.clip((0.85 * right + 1), 0, 255))

        left_mask = grad((pos, height), "h", (50, 50, 50), (0, 0, 0))
        left = cv2.addWeighted(left_light, 1, left_mask, 1, 0.0)

        right_mask = grad((width - pos, height), "h", (50, 50, 50), (0, 0, 0))
        right = cv2.addWeighted(right_light, 1, right_mask, 0.8, 0.0)

        blend = np.hstack([left, right])
        assert blend.shape == img.shape
    else:
        left = img[:pos, :]
        right = img[pos:, :]
        # 分别调整光影
        left_light = np.uint8(np.clip((0.8 * left + 1), 0, 255))
        right_light = np.uint8(np.clip((0.85 * right + 1), 0, 255))

        left_mask = grad((width, pos), "v", (50, 50, 50), (0, 0, 0))
        left = cv2.addWeighted(left_light, 1, left_mask, 1, 0.0)

        right_mask = grad((width, height - pos), "v", (50, 50, 50), (0, 0, 0))
        right = cv2.addWeighted(right_light, 1, right_mask, 0.8, 0.0)

        blend = np.vstack([left, right])
        assert blend.shape == img.shape
    return blend


def add_shader(img,shader=None,alpha=0.5,beta=0.5):
    """按纸张增加阴影"""
    img = as_array(img)
    h, w = img.shape[:2]
    shader = as_array(shader)
    shader = cv2.resize(shader, (w, h))
    shader = cv2.cvtColor(shader,cv2.COLOR_BGR2GRAY)
    shader = cv2.cvtColor(shader,cv2.COLOR_GRAY2BGR)
    return cv2.addWeighted(img, alpha, shader, beta, 0.0)

