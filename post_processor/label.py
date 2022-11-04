"""
标注文件读写修改方法
"""
import cv2
import numpy as np

from post_processor.deco import keepdata


def log_label(out_file, img, data):
    """
    记录保存标注文件和图像
    :param out_file: 文件名
    :param img: 图像
    :param data: 标注数据字典
    :return: None
    """
    labels = data["label"]
    points = data["points"]
    with open(out_file, "w", encoding="utf-8") as file:
        for lno, label in enumerate(labels):
            pts = (
                int(points[lno * 4][0]),
                int(points[lno * 4][1]),
                int(points[lno * 4 + 1][0]),
                int(points[lno * 4 + 1][1]),
                int(points[lno * 4 + 2][0]),
                int(points[lno * 4 + 2][1]),
                int(points[lno * 4 + 3][0]),
                int(points[lno * 4 + 3][1]),
            )
            line = ";".join(map(str, [img, *pts, label]))
            file.write(line + "\n")


def show_label(data):
    """
    在图像上绘制标注框及文字
    :param data: 标注字典
    :return: 新的标注字典
    """
    labels = data["label"]
    points = data["points"]
    img = data["image"]
    for lno, _ in enumerate(labels):
        pts = [
            [int(points[lno * 4][0]), int(points[lno * 4][1])],
            [int(points[lno * 4 + 1][0]), int(points[lno * 4 + 1][1])],
            [int(points[lno * 4 + 2][0]), int(points[lno * 4 + 2][1])],
            [int(points[lno * 4 + 3][0]), int(points[lno * 4 + 3][1])],
        ]
        pts = np.array(pts, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(img, [pts], isClosed=True, color=(0, 255, 0))
    data["image"] = img
    return data
