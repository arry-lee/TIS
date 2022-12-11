"""
各种后处理器的随机效果版本
"""
import os
import random

import cv2
import numpy as np

from postprocessor.background import add_background_data
from postprocessor.convert import keepdata
from postprocessor.distortion import distortion

from postprocessor.curve import bezier_curve
from postprocessor.displace import TEXTURE_DIR, displace
from postprocessor.noise import gauss_noise, pepper_noise
from postprocessor.perspective import perspective_data
from postprocessor.reflect import reflect
from postprocessor.rotate import rotate_data
from postprocessor.spread import spread
from postprocessor.seal import add_seal
from postprocessor.shadow import add_fold, add_shader
from postprocessor.watermark import add_watermark


def random_distortion(data, max_peak, max_period):
    """
    随机扭曲
    :param data: dict 标注字典
    :param max_peak: int 最大峰值
    :param max_period: int 最大周期
    :return: dict 标注字典
    """
    peak = random.uniform(0, max_peak)
    period = random.randint(1, max_period)
    direction = random.choice("xy")
    if data.get("mask", None) is None:
        data["mask"] = np.ones(data["image"].shape[:2], np.uint8) * 255
    data["image"] = distortion(data["image"], peak, period, direction)
    data["mask"] = distortion(data["mask"], peak, period, direction)
    return data


def random_rotate(data, min_angle=-10, max_angle=10):
    """
    随机转动
    :param data: dict 标注字典
    :param min_angle: float最大角度
    :param max_angle: float 最大角度
    :return: dict 标注字典
    """
    angle = random.uniform(min_angle, max_angle)
    return rotate_data(data, angle)


def random_perspective(data, min_offset=0.02, max_offset=0.05):
    """
    随机透视
    :param data: dict 标注字典
    :param min_offset: 最小偏移
    :param max_offset: 最大偏移
    :return: dict 标注字典
    """
    left_offset = random.uniform(min_offset, max_offset)
    right_offset = random.uniform(min_offset, max_offset)
    return perspective_data(data, left_offset, right_offset)


def random_source(source_dir):
    """
    随机资源文件
    :param source_dir: str 资源目录
    :return: path 文件
    """
    return os.path.join(source_dir, random.choice(list(os.listdir(source_dir))))


def random_background(data, bg_dir, min_offset, max_offset):
    """
    随机背景
    :param data: dict 标注字典
    :param bg_dir: str 背景目录
    :param min_offset: int 最小偏移量
    :param max_offset: int 最大偏移量
    :return: dict 标注字典
    """
    background = random_source(bg_dir)
    offset = random.randint(min_offset, max_offset)
    return add_background_data(data, background, offset)


@keepdata
def random_pollution(data, dirty_dir):
    """
    随机污染
    :param data: dict 标注字典
    :param dirty_dir: str 污染资源目录
    :return: dict 标注字典
    """
    watermark = random_source(dirty_dir)
    return add_watermark(data, watermark)


@keepdata
def random_seal(data, seal_dir):
    """
    随机盖章
    :param data: dict 标注字典
    :param seal_dir: str 印章资源目录
    :return: dict 标注字典
    """
    seal = random_source(seal_dir)
    return add_seal(data, seal)


@keepdata
def random_fold(data, min_range=0.25, max_range=0.75):
    """
    随机折痕
    :param data: dict 标注字典
    :param min_range: float 最低范围比率
    :param max_range: float 最高范围比率
    :return: dict 标注字典
    """
    height, width = data.shape[:2]
    direction = random.choice("hv")
    if direction == "h":
        pos = random.randint(int(width * min_range), int(width * max_range))
    else:
        pos = random.randint(int(height * min_range), int(height * max_range))
    return add_fold(data, pos, direction)


@keepdata
def random_noise(data, max_prob=0.02):
    """
    随机噪声
    :param data: dict 标注字典
    :param max_prob: float 最大噪声比例
    :return: dict 标注字典
    """
    prob = random.uniform(0, max_prob)
    return pepper_noise(data, prob)


@keepdata
def random_gauss_noise(data):
    return gauss_noise(data, mean=0.01)


@keepdata
def random_reflect(data, light=None):
    """
    随机反射效果
    :param data: dict 标注字典
    :return: dict
    """
    if not light:
        light = r'E:\00IT\P\uniform\post_processor\tmp\test.jpeg'
    return reflect(data, light)


@keepdata
def random_shadow(data):
    shader = random_source(r"/postprocessor\displace\paper")
    return add_shader(data, shader)


def random_curve(num=5, high=4):
    """
    随机曲线
    :param num: int 控制点数量
    :param high: int 控制点坐标最大值
    :return: np.ndarray 随机曲线图
    """
    pts = np.random.randint(0, high, (num, 2), np.int32)
    color = random.choice(["red", "green", "blue", "black", "yellow"])
    return bezier_curve(pts, color)


def random_ink():
    """随机笔迹"""
    img = random_curve()
    return cv2.blur(spread(img), ksize=(3, 3))


def random_displace(text_layer,ratio=2,paper_dir=TEXTURE_DIR):
    """
    随机置换
    :param text_layer: 文字层
    :return:
    """
    texture = random_source(paper_dir)
    return displace(text_layer, texture, ratio)