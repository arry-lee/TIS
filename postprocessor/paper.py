"""
纸张模拟器模块
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw

from postprocessor.convert import keepdata

WIDTH_IN_MM = 210  # A4 的毫米尺寸
HEIGHT_IN_MM = 279
DIP = 4  # 每毫米像素数量
WIDTH, HEIGHT = WIDTH_IN_MM * DIP, HEIGHT_IN_MM * DIP

white = (244, 244, 244)

left, right, top, bottom = 25 * DIP, 25 * DIP, 20 * DIP, 20 * DIP

TEXTURE_DIR = "../static/paper/"


class Paper:
    """
    纸张模拟类
    """

    def __init__(
        self,
        width=None,
        mode="A4",
        texture=None,
        color=(255, 255, 255),
        dip=4,
        direction="v",
        offset_p=None,
        offset=20,
    ):
        self.mode = mode
        self.direction = direction
        self.texture = texture
        self.color = color
        self.offset = offset
        if self.mode.upper() == "A4":
            self.width_mm = 210
            self.height_mm = 279
        if self.direction == "h":
            self.width_mm, self.height_mm = self.height_mm, self.width_mm
        if not width:
            self.dip = dip
            self.width = self.dip * self.width_mm
            self.height = self.dip * self.height_mm
        else:
            self.width = width
            self.dip = width // self.width_mm
            self.height = self.dip * self.height_mm
        self.size = (self.width, self.height)
        if self.texture:
            self._image = Image.open(self.texture).resize(self.size)
        else:
            self._image = Image.new("RGB", self.size, self.color)
        self._draw = ImageDraw.Draw(self._image)
        if offset_p is not None:
            offset = offset_p // self.dip
        self.pad = (
            offset * self.dip,
            offset * self.dip,
            offset * self.dip,
            offset * self.dip,
        )
        self._box = (
            offset * self.dip,
            offset * self.dip,
            self.width - offset * self.dip,
            self.height - offset * self.dip,
        )
        self.header_box = (0, 0, self.width, offset * self.dip)
        self.footer_box = (0, self.height - offset * self.dip, self.width, self.height)

    @property
    def image(self):
        """纸张图像"""
        # self._draw.rectangle(self._box,outline='black',width=4)
        return self._image

    def set_header(self, text, font):
        """
        设置页眉
        :param text: 文字 str
        :param font: 字体
        :return: None
        """
        pos = self.width // 2, self.header_box[3] // 2
        self._draw.line((0, 10 * DIP) + (self.width, 10 * DIP), fill=(0, 0, 0), width=2)
        self._draw.text(pos, text, fill="black", font=font, anchor="mm")

    @property
    def box(self):
        """页面边框"""
        return self._box

    @box.setter
    def box(self, value):
        if isinstance(value, (tuple, list)) and len(value) == 4:
            self.left, self.top, self.right, self.bottom = value
            self._box = (
                self.left,
                self.top,
                self.width - self.right,
                self.height - self.bottom,
            )


def resize_to_a4_width(image):
    """
    改变图像宽度至A4大小
    :param image: np.ndarray
    :return: np.ndarray
    """
    height, width = image.shape[:2]
    return cv2.resize(image, (WIDTH, int(WIDTH / width * height)))


def print_on_a4(image):
    """
    将图像打印到A4纸上,自适应宽度
    :param image: 原图 np.ndarray
    :return: np.ndarray
    """
    img = resize_to_a4_width(image)
    height, _ = img.shape[:2]
    out = np.ones((HEIGHT, WIDTH, 3), np.uint8) * 244
    out[:height, :] = img[:height, :]
    return out


@keepdata
def add_corner(image, mode="fold"):
    """
    给纸张或图像增加折角效果
    :param image: 图像 ndarray
    :param mode: 折角'fold' or 卷角 'other'
    :return: ndarray
    """
    if mode == "fold":
        corner = cv2.imread("../static/paper/corner_fd.jpg")
    else:
        corner = cv2.imread("../static/paper/corner_br.jpg")

    out = print_on_a4(image)
    height, width = corner.shape[:2]
    out[HEIGHT - height :, WIDTH - width :] = corner
    return out
