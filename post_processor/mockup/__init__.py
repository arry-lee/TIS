"""
下载并处理 mockups 样机
"""
import glob
import json
import os
import random
import re

import cv2
import numpy as np
import requests
import tqdm
from PIL import Image

from post_processor.deco import c2p, p2c
from post_processor.perspective import perspective_points

__all__ = ["Mockup", "random_mockup"]

BASEDIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MOCKUP_DIR = os.path.join(BASEDIR, "res")


def _get_image_urls(path):
    """提取mockup图片"""
    img_pattern = re.compile(
        r'src="(https://images-public\.smartmockups\.com/mockups/.+?_en\.jpg)'
    )
    with open(path) as file:
        text = file.read()
    return img_pattern.findall(text)


def get_mockup(url, cache_dir=None):
    """
    使用磁盘缓存的方式读取网络图片
    :param url: 网络url
    :param cache_dir: 磁盘缓存路径
    :return: Image
    """
    if cache_dir is None:
        cache_dir = "./cache"
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)

    path = os.path.join(cache_dir, url.rsplit("/", 1)[1])

    if not os.path.exists(path):
        response = requests.get(url)
        with open(path, "wb") as file:
            file.write(response.content)

    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    return img


def download_mockups(path, cache_dir):
    """预下载所有的图片"""
    for url in tqdm.tqdm(_get_image_urls(path)):
        get_mockup(url, cache_dir)


# pylint: disable=too-many-arguments
def perspective(
    img,
    points,
    size,
    border_value=(0, 0, 0),
    mask=False,
    matrix=False,
):
    """
    透视变换
    :param img: np.ndarray
    :param points: 四点
    :param size: (w,h)
    :param border_value: 填充色
    :param mask: bool 是否返回 mask
    :param matrix: bool 是否返回变换矩阵
    :return: np.ndarray or Tuple(np.ndarray,bool,bool)
    """
    height, width = img.shape[:2]
    src = np.float32([(0, 0), (width, 0), (0, height), (width, height)])
    dst = np.float32([points[0], points[1], points[3], points[2]])
    mat = cv2.getPerspectiveTransform(src, dst)
    out = cv2.warpPerspective(img, mat, size, borderValue=border_value)

    if mask is True:
        if img.shape[2] == 3:
            mask = np.ones((height, width), np.uint8) * 255
        else:
            mask = img[:, :, 3]
        mask = cv2.warpPerspective(mask, mat, size, borderValue=0)
        if matrix:
            return out, mask, mat
        return out, mask
    if matrix:
        return out, mat
    return out


class Mockup:
    """原本打算用算法提取四个角点，但是通用性太差了，
    所用时间大于人工标注
    所以放弃，直接使用人工标注的
    """

    def __init__(self, fp, points=None, offset=1, crop=False):
        self.origin = Image.open(fp)
        self.origin_points = np.array(points, np.int)

        if crop:  # 可以随机裁剪增加多样性
            points = self._crop(points, offset)
        self.size = self.origin.size
        self.points = self.offset_points(points, offset)

    def _crop(self, points, offset):
        left = min(x[0] for x in points)
        right = max(x[0] for x in points)
        top = min(x[1] for x in points)
        bottom = max(x[1] for x in points)
        topleft = random.randint(0, int(left - offset)), random.randint(
            0, int(top - offset)
        )
        bottomright = random.randint(
            int(right + offset), self.origin.width - 1
        ), random.randint(int(bottom + offset), self.origin.height - 1)
        self.origin = self.origin.crop(topleft + bottomright)
        new_points = []
        for point in points:
            new_points.append([point[0] - topleft[0], point[1] - topleft[1]])
        points = new_points
        return points

    @staticmethod
    def offset_points(points, offset):
        """膨胀"""
        return [
            [points[0][0] - offset, points[0][1] - offset],
            [points[1][0] + offset, points[1][1] - offset],
            [points[2][0] + offset, points[2][1] + offset],
            [points[3][0] - offset, points[3][1] + offset],
        ]

    def perspective(self, img):
        """mockup image"""
        img = cv2.imread(img, cv2.IMREAD_UNCHANGED)
        out = perspective(img, self.points, self.size, border_value=(0, 0, 0, 0))
        out = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGRA2RGBA))
        obg = self.origin.copy()
        obg.paste(out, mask=out)
        return obg

    def perspective_data(self, data):
        """mockup image_data"""
        img, mask, mat = perspective(
            p2c(data["image"]),
            self.points,
            self.size,
            border_value=(0, 0, 0, 0),
            mask=True,
            matrix=True,
        )

        out = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA))
        obg = self.origin.copy()

        if obg.mode == "RGBA":
            mask = cv2.bitwise_and((255 - np.array(obg.getchannel("A"))), mask)

        obg.paste(out, mask=Image.fromarray(mask))
        data["image"] = cv2.cvtColor(np.asarray(obg, np.uint8), cv2.COLOR_RGBA2BGR)
        data["points"] = perspective_points(data["points"], mat)
        data["mask"] = mask
        return data

    @classmethod
    def from_json(cls, file, offset=10, crop=False):
        """
        从json文件读取 mockuo
        :param file: json文件
        :param offset: 偏移量
        :param crop: 是否裁剪
        :return: Mockup 实例
        """
        path = os.path.dirname(file)
        try:
            with open(file, "r", encoding="utf-8") as json_file:
                content = json.load(json_file)
        except UnicodeDecodeError:
            with open(file, "r") as json_file:
                content = json.load(json_file)
        points = content["shapes"][0]["points"]
        name = os.path.join(path, content["imagePath"])
        return cls(name, points, offset, crop)


def random_mockup(image_data, mockup_dir, offset=10, harmonize=None, crop=False):
    """
    随机选择一个样机应用到图片字典上
    :param image_data: dict
    :param mockup_dir: pathlike
    :return: dict
    """
    mockup_dir = os.path.join(DEFAULT_MOCKUP_DIR, mockup_dir)
    print(mockup_dir)
    file = random.choice(glob.glob(os.path.join(mockup_dir, "*.json")))
    mock = Mockup.from_json(file, offset, crop)
    data = mock.perspective_data(image_data)
    if harmonize:
        try:
            data["image"] = harmonize(c2p(data["image"]), data["mask"])
        except RuntimeError:
            return data
    return data
