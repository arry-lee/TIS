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
    peak = random.uniform(0, max_peak)
    period = random.randint(1, max_period)
    direction = random.choice("xy")
    if data.get("mask", None) is None:
        data["mask"] = np.ones(data["image"].shape[:2], np.uint8) * 255

    data["image"] = distortion(data["image"], peak, period, direction)
    data["mask"] = distortion(data["mask"], peak, period, direction)
    return data


def random_rotate(data, min_angle, max_angle):
    angle = random.uniform(min_angle, max_angle)
    return rotate_data(data, angle)


def random_perspective(data, min_offset, max_offset):
    ld = random.uniform(min_offset, max_offset)
    rd = random.uniform(min_offset, max_offset)
    return perspective_data(data, ld, rd)


def random_source(dir):
    return os.path.join(dir, random.choice(list(os.listdir(dir))))


def random_background(data, bg_dir, min_offset, max_offset):
    background = random_source(bg_dir)
    offset = random.randint(min_offset, max_offset)
    return add_background_data(data, background, offset)


@keepdata
def random_pollution(img, dirty_dir):
    watermark = random_source(dirty_dir)
    return add_watermark(img, watermark)


@keepdata
def random_seal(img, seal_dir):
    seal = random_source(seal_dir)
    return add_seal(img, seal)


@keepdata
def random_fold(img, min_range, max_range):
    h, w = img.shape[:2]
    direction = random.choice("hv")
    if direction == "h":
        x = random.randint(int(w * min_range), int(w * max_range))
    else:
        x = random.randint(int(h * min_range), int(h * max_range))
    return add_fold(img, x, direction)


@keepdata
def random_noise(img, max_prob):
    prob = random.uniform(0, max_prob)
    return sp_noise(img, prob)
