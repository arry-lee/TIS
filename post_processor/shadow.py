# 给图片增加渐变和光影
import random
import cv2
import numpy as np


def grad(size, direct, color_start, color_end):
    """创建一个渐变蒙版
    size 图片大小
    direct 方向 h为横向
    color_start 起点颜色
    color_end 终点颜色
    """
    w, h = size
    # 创建一幅与原图片一样大小的透明图片
    grad_img = np.ndarray((h, w, 3), dtype=np.uint8)

    if direct == "h":
        g_b = float(color_end[0] - color_start[0]) / w
        g_g = float(color_end[1] - color_start[1]) / w
        g_r = float(color_end[2] - color_start[2]) / w
        for i in range(h):
            for j in range(w):
                grad_img[i, j, 0] = color_start[0] + j * g_b
                grad_img[i, j, 1] = color_start[1] + j * g_g
                grad_img[i, j, 2] = color_start[2] + j * g_r
    else:
        g_b = float(color_end[0] - color_start[0]) / h
        g_g = float(color_end[1] - color_start[1]) / h
        g_r = float(color_end[2] - color_start[2]) / h
        for i in range(h):
            for j in range(w):
                grad_img[i, j, 0] = color_start[0] + i * g_b
                grad_img[i, j, 1] = color_start[1] + i * g_g
                grad_img[i, j, 2] = color_start[2] + i * g_r

    return grad_img


def add_fold(img, x, direction="h"):
    """加一条折痕的效果
    x 位置
    direction: 'h' 横向,'v'纵向
    """
    # img = imageit(img)
    h, w = img.shape[:2]
    if direction == "h":
        ll = img[:, :x]
        rr = img[:, x:]
        # 分别调整光影
        l = np.uint8(np.clip((0.8 * ll + 1), 0, 255))
        r = np.uint8(np.clip((0.85 * rr + 1), 0, 255))

        left_mask = grad((x, h), "h", (50, 50, 50), (0, 0, 0))
        left = cv2.addWeighted(l, 1, left_mask, 1, 0.0)

        right_mask = grad((w - x, h), "h", (50, 50, 50), (0, 0, 0))
        right = cv2.addWeighted(r, 1, right_mask, 0.8, 0.0)

        blend = np.hstack([left, right])
        assert blend.shape == img.shape
    else:
        ll = img[:x, :]
        rr = img[x:, :]
        # 分别调整光影
        l = np.uint8(np.clip((0.8 * ll + 1), 0, 255))
        r = np.uint8(np.clip((0.85 * rr + 1), 0, 255))

        left_mask = grad((w, x), "v", (50, 50, 50), (0, 0, 0))
        left = cv2.addWeighted(l, 1, left_mask, 1, 0.0)

        right_mask = grad((w, h - x), "v", (50, 50, 50), (0, 0, 0))
        right = cv2.addWeighted(r, 1, right_mask, 0.8, 0.0)

        blend = np.vstack([left, right])
        assert blend.shape == img.shape
    return blend
