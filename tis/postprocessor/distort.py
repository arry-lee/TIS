"""
创建一个虚拟相机，实现图像扭曲效果
"""
import cv2
import numpy as np
from vcam import meshGen, vcam


def distort(img, peak=1.0, period=1, direction="x"):
    """
    将原图扭曲变换，投影到一个3维曲面上
    :param img: 原图
    :param peak: 峰值像素高度
    :param period: 周期数
    :param direction: 方向 x or y
    :return: np.ndarray
    """
    height, width = img.shape[:2]
    cam = vcam(H=height, W=width)
    # 创建一个与输入图像大小相同的网格
    plane = meshGen(height, width)
    # 修改Z的值，默认为1，即平面
    # 将每个3D点的Z坐标定义为Z = 10*sin(2*pi[x/w]*10)
    if direction == "x":
        plane.Z = peak - peak * np.sin((plane.X / plane.W) * 2 * np.pi * period)
    else:
        plane.Z = peak * np.sin((plane.Y / plane.H) * 2 * np.pi * period)
    # 获取得到最终的三维曲面
    pts3d = plane.getPlane()
    # 将三维曲面投影到二维图像坐标
    pts2d = cam.project(pts3d)
    # 使用投影得到的二维点集构建映射函数
    # 这里的二维点集使用三维曲面投影得到
    map_x, map_y = cam.getMaps(pts2d)
    # 将两个映射函数作用与图像，得到最终图像
    output = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR)
    output = cv2.flip(output, 1)
    return output