"""
标注文件读写修改方法
"""
import os

import cv2
import numpy as np
from PIL import Image


def log_label(filename, image, label_info):
    """
    记录保存标注文件和图像
    :param filename: 文件名
    :param image: 图像
    :param label_info: 标注数据字典
    :return: None
    """
    labels = label_info["label"]
    points = label_info["points"]
    with open(filename, "w", encoding="utf-8") as file:
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
            line = ";".join(map(str, [image, *pts, label]))
            file.write(line + "\n")


def show_label(label_info):
    """
    在图像上绘制标注框及文字
    :param label_info: 标注字典
    :return: 新的标注字典
    """
    labels = label_info["label"]
    points = label_info["points"]
    image = label_info["image"]
    for lno, _ in enumerate(labels):
        pts = [
            [int(points[lno * 4][0]), int(points[lno * 4][1])],
            [int(points[lno * 4 + 1][0]), int(points[lno * 4 + 1][1])],
            [int(points[lno * 4 + 2][0]), int(points[lno * 4 + 2][1])],
            [int(points[lno * 4 + 3][0]), int(points[lno * 4 + 3][1])],
        ]
        pts = np.array(pts, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(image, [pts], isClosed=True, color=(0, 255, 0))
    label_info["image"] = image
    return label_info


def save_and_log(label_info, fname, output_dir):
    """
    保存图片和标注到指定文件夹
    :param label_info: dict 图像字典
    :param fname: basename 命名 后缀又具体格式定
    :param output_dir: 输出路径
    :return: None
    """
    image = label_info["image"]
    name = f"{fname}.jpg"
    if isinstance(image, Image.Image):
        if image.mode == "RGBA":
            name = f"{fname}.png"
        image.save(os.path.join(output_dir, name))
    else:
        if image.shape[2] == 4:
            name = f"{fname}.png"
        cv2.imwrite(os.path.join(output_dir, name), image)
    log_label(
        os.path.join(output_dir, "%s.txt" % fname),
        name,
        label_info,
    )