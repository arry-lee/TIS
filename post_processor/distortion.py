import random

import cv2
import numpy as np
from vcam import vcam, meshGen

# 创建一个虚拟相机，并设定输入图像的大小


def distortion(img, peak=1.0, period=1, direction="x"):
    """将原图扭曲变换，投影到一个3维曲面上"""
    H, W = img.shape[:2]
    c1 = vcam(H=H, W=W)
    # 创建一个与输入图像大小相同的网格
    plane = meshGen(H, W)
    # 修改Z的值，默认为1，即平面
    # 将每个3D点的Z坐标定义为Z = 10*sin(2*pi[x/w]*10)
    if direction == "x":
        plane.Z = peak * np.sin((plane.X / plane.W) * 2 * np.pi * period)
    else:
        plane.Z = peak * np.sin((plane.Y / plane.H) * 2 * np.pi * period)
    # 获取得到最终的三维曲面
    pts3d = plane.getPlane()
    # 将三维曲面投影到二维图像坐标
    pts2d = c1.project(pts3d)
    # 使用投影得到的二维点集构建映射函数
    # 这里的二维点集使用三维曲面投影得到
    map_x, map_y = c1.getMaps(pts2d)
    # 将两个映射函数作用与图像，得到最终图像
    output = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR)
    output = cv2.flip(output, 1)
    return output
