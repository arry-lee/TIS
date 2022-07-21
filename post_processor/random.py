"""
各种后处理器的随机效果版本
"""
import os
import random

import numpy as np

from post_processor.background import add_background_data
from post_processor.deco import keepdata
from post_processor.distortion import distortion
from post_processor.noisemaker import sp_noise
from post_processor.perspective import perspective_data
from post_processor.rotation import rotate_data
from post_processor.seal import add_seal
from post_processor.shadow import add_fold
from post_processor.watermark import add_watermark

__all__ = [
    "random_seal",
    "random_noise",
    "random_fold",
    "random_pollution",
    "random_rotate",
    "random_background",
    "random_perspective",
    "random_distortion",
]


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


def random_rotate(data, min_angle, max_angle):
    """
    随机转动
    :param data: dict 标注字典
    :param min_angle: float最大角度
    :param max_angle: float 最大角度
    :return: dict 标注字典
    """
    angle = random.uniform(min_angle, max_angle)
    return rotate_data(data, angle)


def random_perspective(data, min_offset, max_offset):
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
def random_fold(data, min_range, max_range):
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
def random_noise(data, max_prob):
    """
    随机噪声
    :param data: dict 标注字典
    :param max_prob: float 最大噪声比例
    :return: dict 标注字典
    """
    prob = random.uniform(0, max_prob)
    return sp_noise(data, prob)
