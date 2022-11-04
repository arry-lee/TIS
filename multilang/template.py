"""
    template.py 通用的模板格式定义
"""
import json
import math
import os
import pickle
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Tuple

from PIL import Image, ImageDraw, ImageFont
from pyrect import Rect

from awesometable.fontwrap import put_text_in_box
from post_processor.deco import c2p, p2c
from utils.remover import remove_text


class TemplateError(Exception):
    """Template Error"""


@dataclass
class Text:
    """文本框"""

    pos: Tuple[int, int] = None
    text: str = ""
    font: Any = None
    anchor: str = "lt"
    color: Any = "black"
    rect: Rect = None  # 矩形框


class Template:
    """模板类
    模板包含一个背景图片和若干标注框
    """

    ext = "tpl"
    default_font = "simfang.ttf"

    def __init__(self, image, texts):
        self.image = image
        self.texts = texts
        self.path = None

    def render(self):
        """
        渲染模板成图片
        :return:
        """
        return self.render_image_data()["image"]

    def render_image_data(self):
        """
        渲染模板成图片字典格式,包含标注
        :return:
        """
        image = self.image.copy()
        text_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
        text_drawer = ImageDraw.Draw(text_layer)

        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(image)
        mask_draw = ImageDraw.Draw(mask)
        text_list = []
        for text in self.texts:
            if text.text in ("<LTImage>", "IMAGE", "image@"):
                continue

            if text.text.startswith("key@"):  # 固定位置的文字不重写
                text_box = [
                    text.rect.left,
                    text.rect.top,
                    text.rect.right,
                    text.rect.bottom,
                ]
                text_list.append([text_box, "text@" + text.text.removeprefix("key@")])
                continue

            if text.font is None or text.font.lower() in ("b", "i"):
                # 原始模板，没填充的
                draw.rectangle(
                    (text.rect.left, text.rect.top, text.rect.right, text.rect.bottom),
                    outline=random_color(),
                    width=2,
                )
                font = ImageFont.truetype(self.default_font, text.rect.height)
            else:
                font = ImageFont.truetype(text.font, text.rect.height)
                draw.text((text.rect.left, text.rect.top), text.text, text.color, font)
                text_drawer.text(
                    (text.rect.left, text.rect.top), text.text, text.color, font
                )
                mask_draw.text(
                    (text.rect.left, text.rect.top),
                    text.text,
                    255,
                    font,
                    stroke_fill=255,
                    stroke_width=0,
                )

            text_list.append(
                [
                    draw.textbbox((text.rect.left, text.rect.top), text.text, font),
                    "text@" + text.text,
                ]
            )

        boxes = [tb[0] for tb in text_list]
        label = [tb[1] for tb in text_list]
        points = []
        for box in boxes:
            points.append([box[0], box[1]])
            points.append([box[2], box[1]])
            points.append([box[2], box[3]])
            points.append([box[0], box[3]])

        return {
            "image": image,
            "boxes": boxes,
            "label": label,
            "points": points,
            "mask": mask,
            "text_layer": text_layer,
            "background": self.image.copy(),
        }

    def __setstate__(self, state):
        self.image = state["image"]
        self.texts = state["texts"]

    def __getstate__(self):
        return {"image": self.image, "texts": self.texts}

    def save(self, path):
        """将实例保存成模板文件"""
        with open(path, "wb") as file:
            pickle.dump(self, file)

    @staticmethod
    def _fill_text(sentence, text):
        """将句子放进text里面"""
        return put_text_in_box(
            sentence,
            text.rect.width,
            "black",
            text.font,
            text.rect.height,
            break_word=False,
        )[0].splitlines()[0]

    def replace_text(self, engine, translator=None):
        """
        替换模板文本,此处策略和具体文件有关
        :param translator: 翻譯引擎
        :param engine: 使用的引擎，可以是Faker，可以是Trans
        :return: None
        """
        normal_font = engine.font()
        bold_font = engine.font("b")

        for text in self.texts:
            if text.text in ("<LTImage>", "IMAGE", "image@"):  # 忽略图片区域
                continue
            if text.font is None:  # 分配字体
                text.font = normal_font
            elif text.font == "b":
                text.font = bold_font

            if text.text.strip().isdigit():  # 不改变数字
                text.text = text.text.strip()
                continue

            if not translator:  # 不是翻译
                font = ImageFont.truetype(text.font, text.rect.height)
                text.text = engine.sentence_fontlike(font, text.rect.width).title()
            else:
                try:
                    trans_text = translator.translate(text.text.strip())
                except KeyError:
                    font = ImageFont.truetype(text.font, text.rect.height)
                    text.text = engine.sentence_font_like(font, text.rect.width)
                else:
                    text.text = str(trans_text)

    def clean_texts(self):
        """清除文本"""
        for text in self.texts:
            text.text = ""

    @staticmethod
    def load(path):
        """从模板文件加载模板实例"""
        with open(path, "rb") as file:
            obj = pickle.load(file)
        return obj

    def get_background(self):
        """将每个文本切片移除文字后回填"""
        image = p2c(self.image)
        for text in self.texts:
            top, bottom, left, right = (
                text.rect.top,
                text.rect.bottom,
                text.rect.left,
                text.rect.right,
            )
            img = image[top:bottom, left:right]
            new_img = remove_text(img, text.text)
            image[top:bottom, left:right] = new_img
            break
        image = c2p(image)
        image.save("background.jpg")
        self.image = image

    # """
    # @classmethod
    # def from_image(cls, image, ocr_engine=None):
    #     if ocr_engine is None:
    #         try:
    #             from paddleocr import PaddleOCR
    #         except ImportError:
    #             raise ImportError("paddlecor not installed and ocr engine is None")
    #         else:
    #             os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    #             ocr_engine = PaddleOCR(lang="zh")
    #
    #     path = os.path.abspath(image)
    #     image = Image.open(path)
    #     image = c2p(get_background(image))
    #     results = ocr_engine.ocr(image)
    #     texts = []
    #     for box, content in results:
    #         text, _ = content
    #         texts.append(
    #             Text(
    #                 text=text,
    #                 rect=Rect(
    #                     box[0][0],
    #                     box[0][1],
    #                     box[2][0] - box[0][0],
    #                     box[2][1] - box[0][1],
    #                 ),
    #             )
    #         )
    #
    #     return cls(image, texts)
    # """

    @classmethod
    def from_txt(cls, file):
        """
        从标注文件加载模板实例
        :param file: 标注文件路径
        :return: Template 实例
        """
        path = os.path.abspath(file)
        dirname = os.path.dirname(path)
        fontsdir = os.path.join(dirname, "fonts")
        with open(path, encoding="utf-8") as fin:
            txt = fin.read()
        name, tempdict = cls.parse_label_file(txt)
        image = Image.open(os.path.join(dirname, name))
        texts = []
        for box, content in tempdict["text"]:
            if "|" in content:
                text, font = content.split("|")
                font = os.path.join(fontsdir, font)
            else:
                text = content
                font = None
            texts.append(
                Text(
                    text=text,
                    rect=Rect(
                        box[0][0],
                        box[0][1],
                        box[2][0] - box[0][0],
                        box[2][1] - box[0][1],
                    ),
                    font=font,
                )
            )
        return cls(image, texts)

    @staticmethod
    def parse_label_file(template_txt):
        """解析标注文件文本"""
        name = ""
        temp_list = template_txt.splitlines(keepends=False)
        pat = re.compile(
            r"(?P<name>.+);(?P<x1>\d+);(?P<y1>\d+);"
            r"(?P<x2>\d+);(?P<y2>\d+);(?P<x3>\d+);"
            r"(?P<y3>\d+);(?P<x4>\d+);(?P<y4>\d+);"
            r"(?P<label>.+)@(?P<content>.*)"
        )
        temp_dict = defaultdict(list)
        for line in temp_list:
            matched = pat.match(line)
            if matched:
                name = matched["name"]
                box = [
                    [int(matched["x1"]), int(matched["y1"])],
                    [int(matched["x2"]), int(matched["y2"])],
                    [int(matched["x3"]), int(matched["y3"])],
                    [int(matched["x4"]), int(matched["y4"])],
                ]
                label = matched["label"]
                content = matched["content"]
                if label == "table":
                    temp_dict["table"] = [box, content]
                elif label == "row":
                    temp_dict["rows"].append(box)
                elif label == "column":
                    temp_dict["cols"].append(box)
                elif label == "cell":
                    temp_dict["cells"].append(box)
                else:
                    temp_dict["text"].append([box, content])
        if not name:
            raise ValueError("Wrong Format Label File!")
        return name, temp_dict

    def modify_texts(self):
        """修正模板的矩形"""
        modify_rects(self.texts)

    def adjust_texts(self):
        """调整模板的文本框，移除重叠的"""
        self.texts = remove_col(self.texts)

    def show(self):
        """显示模板效果"""
        self.render().show()

    def set_background(self, img):
        """设置模板背景"""
        size = self.image.size
        if isinstance(img, (tuple, str)):
            img = Image.new("RGB", size, img)
        self.image = img.resize(size)

    @classmethod
    def from_json(cls, file):
        """
        从json格式文件读取
        :param file: 文件名
        :return: Template
        """
        texts = []
        path = os.path.dirname(file)
        with open(file, "r", encoding="utf-8") as json_file:
            content = json.load(json_file)
            image = Image.open(os.path.join(path, content["imagePath"]))
            for one in content["shapes"]:
                label = one["label"]
                try:
                    _, text = label.split("@", 1)
                except IndexError:
                    text = label
                points = one["points"]
                texts.append(
                    Text(
                        text=text,
                        rect=Rect(
                            points[0][0],
                            points[0][1],
                            points[1][0] - points[0][0],
                            points[1][1] - points[0][1],
                        ),
                    )
                )
        return cls(image, texts)

    def add_round_corner(self, radius=40):
        """增加圆角"""
        size = self.image.size
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0) + size, radius, fill=255)
        self.image.putalpha(mask)


def random_color():
    """随机色"""
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


def collide_any(rect, others):
    """
    矩形碰撞判断
    :param rect: Rect
    :param others: List[Rect]
    :return: bool
    """
    for other in others:
        if rect.collide(other) and math.isclose(rect.area, other.area, rel_tol=0.1):
            return True
    return False


def remove_col(texts):
    """去除有碰撞的内容"""
    outs = []
    seen = set()
    seen_rect = []
    for text in texts:
        if text.rect.box not in seen and not collide_any(text.rect, seen_rect):
            outs.append(text)
            seen.add(text.rect.box)
            seen_rect.append(text.rect)
    return outs


def modify_rects(texts):
    """
    # 修正矩形的宽度为最小单位的整数倍
    # 修正矩形的坐标到最小单位的整数倍的格点上
    :param texts:
    :return:
    """
    minw, minh = _min_unit(texts)
    for text in texts:
        text.rect.width = round(text.rect.width / minw) * minw
        text.rect.height = round(text.rect.height / minh) * minh
        text.rect.left = round(text.rect.left / minw) * minw
        text.rect.bottom = round(text.rect.bottom / (minh // 2)) * minh // 2


def _get_min_max(texts):
    texts.sort(key=lambda t: t.rect.width)
    min_w = texts[0].rect.width // (len(texts[0].text) + 1)
    max_w = texts[-1].rect.width
    texts.sort(key=lambda t: t.rect.height)
    min_h = texts[0].rect.height
    max_h = texts[-1].rect.height
    return min_w, min_h, max_w, max_h


def _min_unit(texts):
    """
    返回矩形的最小尺寸的一半作为最小尺寸颗粒
    :param texts: List[Text]
    :return: int
    """
    min_width = min(text.rect.width for text in texts)
    max_width = max(text.rect.width for text in texts)
    min_height = min(text.rect.height for text in texts)

    min_width = max_width // (max_width // min_width)
    if min_height % 2:
        min_height -= 1
    return min_width, min_height
