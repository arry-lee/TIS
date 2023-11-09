"""
透视变换模块
"""
import cv2
import numpy as np

from postprocessor.convert import as_array


def perspective(
    img,
    left_offset=0.02,
    right_offset=0.02,
    border_value=(0, 0, 0),
    mask=False,
    matrix=False,
):
    """
    透视变换并且填充背景
    假定下面两点是不动的,左上边点向右偏移 ld，右上点向左偏移 rd；
    :param img: np.ndarray
    :param left_offset: float 左上角向右偏移比例
    :param right_offset: float 右上角向左偏移比例
    :param border_value: 填充色
    :param mask: bool 是否返回 mask
    :param matrix: bool 是否返回变换矩阵
    :return: np.ndarray or Tuple(np.ndarray,bool,bool)
    """
    img = as_array(img)
    height, width = img.shape[:2]
    src = np.float32([(0, 0), (width, 0), (0, height), (width, height)])
    dst = np.float32(
        [
            (width * left_offset, 0),
            (width - width * right_offset, 0),
            (0, height),
            (width, height),
        ]
    )
    mat = cv2.getPerspectiveTransform(src, dst)
    out = cv2.warpPerspective(img, mat, [width, height], borderValue=border_value)
    if not mask and not matrix:
        return out
    if mask is True:
        mask = np.ones((height, width), np.uint8) * 255
        mask = cv2.warpPerspective(mask, mat, [width, height], borderValue=0)
        if matrix:
            return out, mask, mat
        else:
            return out, mask
    if matrix:
        return out, mat


def _trans(points, matrix):
    points = np.array(points)
    height, _ = points.shape
    nps = np.ones((height, 3), np.uint32)
    nps[:, :2] = points
    out = np.array(np.matmul(nps, matrix.T))
    return out


def perspective_points(points, matrix):
    """
    经过透视变化后的点坐标
    :param points: list[list[int,int]] 点坐标列表
    :param matrix: 所使用的变换矩阵
    :return: np.ndarray 变换后的坐标
    """
    pts = _trans(points, matrix)
    pts[:, 0] = np.round(pts[:, 0] // pts[:, 2])
    pts[:, 1] = np.round(pts[:, 1] // pts[:, 2])
    points = np.array(pts[:, :2], np.uint32)
    return points


def perspective_data(data, left_offset=0.05, right_offset=0.05, border_value=(0, 0, 0)):
    """
    透视变换标注字典，变换图像的同时更新标注信息
    :param data: dict标注字典
    :param left_offset: float 左上角向右偏移比例
    :param right_offset: float 右上角向左偏移比例
    :param border_value: 填充色
    :return: dict 标注字典
    """
    data["image"], mask, mat = perspective(
        data["image"], left_offset, right_offset, border_value, mask=True, matrix=True
    )
    data["points"] = perspective_points(data["points"], mat)
    if data.get("mask", None) is not None:
        data["mask"] = perspective(data["mask"], left_offset, right_offset)
    else:
        data["mask"] = mask
    return data
