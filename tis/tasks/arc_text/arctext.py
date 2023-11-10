import math
import random

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


from perspective import perspective_data
from rotation import rotate_data


def p2c(image):
    return cv2.cvtColor(np.asarray(image, np.uint8), cv2.COLOR_RGBA2BGRA)


def c2p(image):
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA))


def _compute_xy(xy, radius, theta, sign, offset, rotation):
    x0, y0 = xy
    dx1 = (radius + offset) * math.sin(theta)
    dy1 = sign * (radius - (radius + offset) * math.cos(theta))

    x1 = int(x0 + dx1)
    y1 = int(y0 + dy1)
    if rotation:
        r1 = math.sqrt(dx1 * dx1 + dy1 * dy1)
        if dx1 != 0:
            if dx1 < 0:
                th = -rotation + math.atan(dy1 / abs(dx1))
                x1 = int(x0 - r1 * math.cos(th))
                y1 = int(y0 + r1 * math.sin(th))
            else:
                th = rotation + math.atan(dy1 / dx1)
                x1 = int(x0 + r1 * math.cos(th))
                y1 = int(y0 + r1 * math.sin(th))
    return x1, y1


def arc_text(
    im,
    xy,
    text,
    font,
    fill="auto",
    radius=200,
    clockwise=True,
    close_ratio=0.7,
    circle=False,
    rotation=0,
    hor=False,
    **kwargs
):
    x0, y0 = xy
    fs = font.size
    if not circle:
        d = 2 * math.asin(close_ratio * fs * math.sqrt(2) / 2 / radius)
    else:
        d = math.pi * 2 / len(text)

    sign = 1 if clockwise else -1

    if hor:
        rotation = -d * (len(text) - 1) * sign / 2
    else:
        rotation = math.radians(rotation)

    if fill == "auto":
        color = (255, 255, 255, 255)
    else:
        color = fill

    up_points = []
    bottom_points = []
    text = text

    for i, char in enumerate(text):
        x, y = _compute_xy((x0, y0), radius, d * i, sign, 0, rotation)

        if i == 0:
            up_points.append(
                _compute_xy((x0, y0), radius, -d / 2, sign, fs / 2, rotation)
            )
            bottom_points.append(
                _compute_xy((x0, y0), radius, -d / 2, sign, -fs / 2, rotation)
            )
        up_points.append(_compute_xy((x0, y0), radius, d * i, sign, fs / 2, rotation))
        bottom_points.append(
            _compute_xy((x0, y0), radius, d * i, sign, -fs / 2, rotation)
        )
        if i == len(text) - 1:
            up_points.append(
                _compute_xy((x0, y0), radius, d * i + d / 2, sign, fs / 2, rotation)
            )
            bottom_points.append(
                _compute_xy((x0, y0), radius, d * i + d / 2, sign, -fs / 2, rotation)
            )

        txt = Image.new("RGBA", (fs, fs), (0, 0, 0, 0))
        draw_txt = ImageDraw.Draw(txt)

        draw_txt.text(
            (0, 0), char, color, font, stroke_fill=(125, 125, 125, 255), stroke_width=2
        )
        txt = txt.rotate(math.degrees(-i * d * sign - rotation), expand=True)
        w, h = txt.size
        im.paste(txt, (x - w // 2, y - h // 2), txt)

    points = up_points + list(reversed(bottom_points))
    # mask = Image.new("RGBA", im.size, (0, 0, 0, 0))
    # draw = ImageDraw.Draw(mask)
    # draw.polygon(points, fill=(0,255,0,100))
    # im.paste(mask,(0,0),mask)
    return im, points


class ArcText(object):
    def __init__(
        self,
        text,
        font_path,
        font_size,
        fill="auto",
        radius=200,
        clockwise=True,
        close_ratio=0.7,
        circle=False,
        rotation=0,
        hor=False,
        **kwargs
    ):
        im = Image.new("RGBA", (2000, 2000), (255, 255, 255, 0))
        xy = (1000, 1000)
        font = ImageFont.truetype(font_path, font_size)
        im, points = arc_text(
            im,
            xy,
            text,
            font,
            fill,
            radius,
            clockwise,
            close_ratio,
            circle,
            rotation,
            hor,
            **kwargs
        )
        xmin, ymin = 99999, 99999
        xmax, ymax = 0, 0
        for x, y in points:
            xmin = min(x, xmin)
            xmax = max(x, xmax)
            ymin = min(y, ymin)
            ymax = max(y, ymax)

        self.image = im.crop((xmin, ymin, xmax, ymax))
        self.points = np.array(points) - np.array([xmin, ymin])
        self.label = "text@" + text

        self._data = {
            "image": self.image,
            "points": [self.points],
            "label": [self.label],
        }

    def get_image(self):
        return self._data

    @property
    def table_width(self):
        return self.image.width

    @table_width.setter
    def table_width(self, val):
        self._table_width = val


class StraightText(object):
    def __init__(
        self,
        text,
        font_path,
        font_size,
        fill="auto",
        rotation=0,
        ver=False,
        perspective=False,
    ):
        font = ImageFont.truetype(font_path, font_size)
        w, h = font.getsize(text, stroke_width=2)
        im = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        draw = ImageDraw.Draw(im)

        draw.text(
            (w // 2, h // 2),
            text,
            fill,
            font,
            stroke_fill=(125, 125, 125, 255),
            stroke_width=2,
            anchor="mm",
        )
        # box = draw.textbbox((0,0),text,font, stroke_width=2)
        # points = [box[0],box[1],(box[2],box[1]),(box[2],box[3]),(box[0],box[3])]
        points = [(0, 0), (w - 1, 0), (w - 1, h - 1), (0, h - 1)]
        self.image = im
        self.points = points
        self.label = "text@" + text

        _data = {"image": p2c(self.image), "points": self.points, "label": [self.label]}

        if ver:
            rotation = 90
        if perspective:
            _data = perspective_data(_data, 0.05, 0.05, borderValue=(255, 255, 255, 0))
        if rotation:
            _data = rotate_data(_data, rotation, borderValue=(255, 255, 255, 0))

        self._data = {
            "image": c2p(_data["image"]),
            "points": [np.array(_data["points"])],
            "label": _data["label"],
        }

    def get_image(self):
        return self._data

    @property
    def table_width(self):
        return self.image.width

    @table_width.setter
    def table_width(self, val):
        self._table_width = val
