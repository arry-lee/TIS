"""
旋转变换模块
"""
import cv2
import numpy as np


def rotate_bound(image, angle, border_value=(0, 0, 0), mask=False, matrix=False):
    """
    旋转图片，扩展边界
    :param image: np.ndarray
    :param angle: degree
    :param border_value: 边界填充色
    :param mask: bool 是否返回 mask
    :param matrix: bool 是否返回 变换矩阵
    :return: np.ndarray|tuple
    """
    height, width = image.shape[:2]
    c_x, c_y = width // 2, height // 2
    mat = cv2.getRotationMatrix2D((c_x, c_y), angle, 1.0)
    cos = np.abs(mat[0, 0])
    sin = np.abs(mat[0, 1])
    # compute the new bounding dimensions of the image
    n_w = int((height * sin) + (width * cos))
    n_h = int((height * cos) + (width * sin))
    # adjust the rotation matrix to take into account translation
    mat[0, 2] += (n_w / 2) - c_x
    mat[1, 2] += (n_h / 2) - c_y
    # perform the actual rotation and return the image
    out = cv2.warpAffine(image, mat, (n_w, n_h), borderValue=border_value)
    if mask:
        mask = np.ones((height, width), np.uint8) * 255
        mask = cv2.warpAffine(mask, mat, (n_w, n_h), borderValue=0)
        if matrix:
            return out, mask, mat
        return out, mask
    if matrix:
        return out, mat
    return out


def rotate_points(points, matrix):
    """
    旋转原始点，得到新的点坐标
    :param points: list[list[int,int]] 坐标列表
    :param matrix: np.ndarray 旋转矩阵
    :return: np.ndarray 新的点坐标
    """
    points = np.array(points)
    height, _ = points.shape
    nps = np.ones((height, 3), np.uint32)
    nps[:, :2] = points
    out = np.array(np.matmul(nps, matrix.T))
    return out


def rotate_data(data, angle=0, border_value=(0, 0, 0)):
    """
     旋转标注字典
    :param data: dict 标注信息字典
    :param angle: float 角度
    :param border_value: tuple 填充色
    :return: dict 新的标注字典
    """
    data["image"], mask, mat = rotate_bound(
        data["image"], angle=angle, border_value=border_value, mask=True, matrix=True
    )
    data["points"] = rotate_points(data["points"], mat)
    if data.get("mask", None) is not None:
        data["mask"] = rotate_bound(
            data["mask"], angle=angle, border_value=border_value
        )
    else:
        data["mask"] = mask
    return data
