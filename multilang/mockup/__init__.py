# 下载并处理mockups
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


def get_image_urls(fp):
    img_pattern = re.compile(
        r'src="(https://images-public\.smartmockups\.com/mockups/.+?_en\.jpg)'
    )
    with open(fp) as f:
        text = f.read()
    ls = img_pattern.findall(text)
    return ls


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


def download_mockups(fp, cache_dir):
    """预下载所有的图片"""
    for url in tqdm.tqdm(get_image_urls(fp)):
        get_mockup(url, cache_dir)


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
    :param left_offset: float 左上角向右偏移比例
    :param right_offset: float 右上角向左偏移比例
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
    if not mask and not matrix:
        return out
    if mask is True:
        if img.shape[2] == 3:
            mask = np.ones((height, width), np.uint8) * 255
        else:
            mask = img[:, :, 3]
        mask = cv2.warpPerspective(mask, mat, size, borderValue=0)
        if matrix:
            return out, mask, mat
        else:
            return out, mask
    if matrix:
        return out, mat


class Mockup:
    """原本打算用算法提取四个角点，但是通用性太差了，所用时间大于人工标注
    所以放弃，直接使用人工标注的
    """

    def __init__(self, fp, points=None, offset=1, crop=False):
        self.origin = Image.open(fp)
        self.origin_points = np.array(points, np.int)

        if crop:  # 可以随机裁剪增加多样性
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
            # self.origin_points = self.origin_points - np.array(topleft)
            new_points = []
            for p in points:
                new_points.append([p[0]-topleft[0],p[1]-topleft[1]])
            points = new_points
        self.size = self.origin.size
        self.points = self.offset_points(points, offset)

    @staticmethod
    def offset_points(points, o):
        return [
            [points[0][0] - o, points[0][1] - o],
            [points[1][0] + o, points[1][1] - o],
            [points[2][0] + o, points[2][1] + o],
            [points[3][0] - o, points[3][1] + o],
        ]

    def perspective(self, img):
        img = cv2.imread(img, cv2.IMREAD_UNCHANGED)
        out = perspective(img, self.points, self.size, border_value=(0, 0, 0, 0))
        out = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGRA2RGBA))
        bg = self.origin.copy()
        bg.paste(out, mask=out)
        return bg

    def perspective_data(self, data):
        img, mask, mat = perspective(
            p2c(data["image"]),
            self.points,
            self.size,
            border_value=(0, 0, 0, 0),
            mask=True,
            matrix=True,
        )

        out = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA))
        bg = self.origin.copy()

        if bg.mode == "RGBA":
            mask = cv2.bitwise_and((255 - np.array(bg.getchannel("A"))), mask)

        bg.paste(out, mask=Image.fromarray(mask))
        data["image"] = cv2.cvtColor(np.asarray(bg, np.uint8), cv2.COLOR_RGBA2BGR)
        data["points"] = perspective_points(data["points"], mat)
        data["mask"] = mask
        return data

    @classmethod
    def from_json(cls, file, offset=10, crop=False):
        path = os.path.dirname(file)
        try:
            with open(file, "r", encoding="utf-8") as fp:
                js = json.load(fp)
        except UnicodeDecodeError:
            with open(file, "r") as fp:
                js = json.load(fp)
        points = js["shapes"][0]["points"]
        name = os.path.join(path, js["imagePath"])
        return cls(name, points, offset, crop)

    # @property
    # def mask(self):
    #     """生成这张背景图的mask"""
    #     w,h = self.size
    #     img = p2c(self.origin).copy()
    #     seed = np.mean(self.origin_points,axis=0).astype(np.int)
    #     msk = np.zeros([h + 2, w + 2], np.uint8)
    #     cv2.floodFill(img, msk, seed, (0, 255, 255), (50, 50, 50),(50, 50, 50), cv2.FLOODFILL_FIXED_RANGE)
    #     msk = np.array(img==(0,255,255))*255
    #     return msk


def random_mockup(image_data, mockup_dir, offset=10, harmonize=None, crop=False):
    """
    随机选择一个样机应用到图片字典上
    :param image_data: dict
    :param mockup_dir: pathlike
    :return: dict
    """
    file = random.choice(glob.glob(os.path.join(mockup_dir, "*.json")))
    mock = Mockup.from_json(file, offset, crop)
    data = mock.perspective_data(image_data)
    if harmonize:
        try:
            data["image"] = harmonize(c2p(data["image"]), data["mask"])
        except RuntimeError:
            return data
    return data


if __name__ == "__main__":
    m = Mockup.from_json("./res/hand/微信图片_2022110216502313.json", 0)
    cv2.imwrite("3.jpg", m.mask)
