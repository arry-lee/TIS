"""
    template.py 通用的模板格式定义
"""
import json
import math
import os
import pickle
import random
import re
import string
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from arc_text.picsum import rand_image
from pyrect import Rect

from awesometable.fontwrap import put_text_in_box
from multifaker import Faker
from poison import poison_text
from post_processor.deco import as_cv, c2p, p2c
from utils.picsum import rand_person
from utils.remover import remove_text

default_engine = Faker('id')


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


def is_nums(text):
    return bool(re.match("\d+", text))


def has_digit(text):
    for i in text:
        if i.isdigit() or i in string.punctuation:
            return True
    return False


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
    
    def render_background(self):
        # texts = []
        for text in self.texts:
            if text.text == "<LTImage>":
                try:
                    self.image.paste(rand_image(*text.rect.size),
                                     text.rect.topleft)
                except:
                    pass
        #     else:
        #         texts.append(text)
        # self.texts = texts
        #
    
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
        text_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
        text_drawer = ImageDraw.Draw(text_layer)
        
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(image)
        mask_draw = ImageDraw.Draw(mask)
        text_list = []
        for text in self.texts:
            if text.text in ("<LTImage>", "IMAGE", "image@"):
                continue
            
            if text.text.startswith("key@"):  # 固定位置的文字不重写
                text_box = [text.rect.left, text.rect.top, text.rect.right,
                            text.rect.bottom]
                text_list.append(
                    [text_box, "text@" + text.text.removeprefix("key@")])
                continue
            
            if text.font is None or text.font.lower() in ("b", "i"):
                # """原始模板，没填充的"""
                draw.rectangle(
                    (text.rect.left, text.rect.top, text.rect.right,
                     text.rect.bottom),
                    outline=random_color(),
                    width=2,
                )
                font = ImageFont.truetype(self.default_font, text.rect.height)
            else:
                size = text.rect.height  # - 4
                # 重新居中渲染
                # print(text.font)
                try:
                    font = ImageFont.truetype(text.font, size)
                except Exception as e:
                    print(e)
                    print(text.font)
                # 如果字宽小于框宽或字符串单词数较少
                draw.text((text.rect.left, text.rect.top), text.text,
                          text.color, font)
                text_drawer.text((text.rect.left, text.rect.top), text.text,
                                 text.color, font)
                mask_draw.text((text.rect.left, text.rect.top), text.text,
                               255, font, stroke_fill=255, stroke_width=0)
                # mask_draw.rectangle((text.rect.left,text.rect.top,text.rect.right,text.rect.bottom),(255,255,255,255))
            
            text_box = draw.textbbox((text.rect.left, text.rect.top), text.text,
                                     font)
            text_list.append([text_box, "text@" + text.text])
        
        boxes = [tb[0] for tb in text_list]
        label = [tb[1] for tb in text_list]
        points = []
        for box in boxes:
            points.append([box[0], box[1]])
            points.append([box[2], box[1]])
            points.append([box[2], box[3]])
            points.append([box[0], box[3]])
        
        return {
            "image"     : image,
            # cv2.cvtColor(np.array(image, np.uint8),cv2.COLOR_RGB2BGR),
            "boxes"     : boxes,  # box 和 label是一一对应的
            "label"     : label,
            "points"    : points,
            "mask"      : mask,
            'text_layer': text_layer,
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
        # comma = sentence[-1]
        # if comma.isalpha():
        #     comma = ""
        
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
            else:
                if not translator:  # 不是翻译
                    font = ImageFont.truetype(text.font, text.rect.height)
                    text.text = engine.sentence_fontlike(font,
                                                         text.rect.width).title()
                    # text.text = engine.sentence_like(text.text,text.rect.width).title()
                    
                    # text.text = self._fill_text(engine.sentence(16), text)
                else:
                    try:
                        trans_text = translator.translate(text.text.strip())
                    except KeyError:
                        font = ImageFont.truetype(text.font, text.rect.height)
                        text.text = engine.sentence_font_like(font,
                                                              text.rect.width)
                        
                        # trans_text = self._fill_text(engine.sentence(16), text)
                    else:
                        text.text = str(trans_text)
    
    def clean_texts(self):
        """清除文本"""
        for text in self.texts:
            text.text = ""
    
    @staticmethod
    def load(path):
        """从模板文件加载模板实例"""
        try:
            with open(path, "rb") as file:
                obj = pickle.load(file)
        except FileNotFoundError:
            raise TemplateError(f"{path} is not a Template File")
        return obj
    
    @classmethod
    def from_pdf(cls, file):
        """从pdf文件加载模板实例"""
        return NotImplemented
    
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
    
    # @classmethod
    # def from_image(cls, image, ocr_engine=None):
    #     """
    #     从图片识别模板
    #     :param image: 图像文件名
    #     :param ocr_engine: OCR 引擎，若未设置会尝试导入 PaddleOcr
    #     :return: Template 实例
    #     """
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
            img = Image.new('RGB', size, img)
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
        with open(file, "r", encoding="utf-8") as fp:
            js = json.load(fp)
            image = Image.open(os.path.join(path, js["imagePath"]))
            for one in js["shapes"]:
                label = one["label"]
                try:
                    key, text = label.split("@", 1)
                except:
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
        size = self.image.size
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0) + size, radius, fill=255)
        self.image.putalpha(mask)


def random_color():
    """随机色"""
    return random.randint(0, 255), random.randint(0, 255), random.randint(0,
                                                                          255)


def collide_any(rect, others):
    """
    矩形碰撞判断
    :param rect: Rect
    :param others: List[Rect]
    :return: bool
    """
    for other in others:
        if rect.collide(other) and math.isclose(rect.area, other.area,
                                                rel_tol=0.1):
            return True
        # if other.collde(rect):
        #     return True
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
        text.rect.left = round(text.rect.left / (minw)) * minw
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


def get_background(img, thresh=128, ksize=(3, 3), iterations=2,
                   inpaint_radius=5):
    """
    移除图像中的文字，获取单纯的背景
    :param img: 图像
    :param thresh: 二值化的阈值
    :param ksize: 膨胀操作的核尺寸
    :param iterations: 膨胀操作的迭代次数
    :param inpaint_radius: 修复操作的半径
    :return: 背景图像
    """
    img = as_cv(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones(ksize, dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations)  # 膨胀
    # mask = cv2.erode(mask, kernel, iterations=1) #腐蚀
    out = cv2.inpaint(img, mask, inpaint_radius, cv2.INPAINT_TELEA)
    cv2.imwrite("mask.jpg", mask)
    cv2.imwrite("bg.jpg", out)
    return out


def get_texts_from_photoshop_html(file):
    """
    从 photoshop 切片导出的 html 中提取texts
    :param file: html文件
    :return: list
    """
    path = os.path.dirname(file)
    name_pat = re.compile(
        r"status='(?P<name>.+)'"
    )  # .+width="(?P<w>\d+)" height="(?P<h>\d+)" border="0" alt="(?P<x>\d+),(?P<y>\d+)"
    pos_pat = re.compile(
        r'width="(?P<w>\d+)" height="(?P<h>\d+)" border="0" alt="(?P<x>\d+),(?P<y>\d+),(?P<font>.+)"'
    )
    with open(file, "r", encoding="utf-8") as fp:
        text = fp.read()
    res = name_pat.findall(text, re.M)
    rects = pos_pat.findall(text, re.M)
    if not len(res) == len(rects):
        print(len(res))
        print(res)
        print(len(rects))
        print(rects)
        raise ValueError("标签或坐标缺失")
    texts = []
    for name, (w, h, x, y, font) in zip(res, rects):
        color = "black"
        if font == "none":
            font = None
        elif "#" in font:
            font, color = font.split("#")
            font = os.path.join(path, font)
            color = "#" + color
        else:
            font = os.path.join(path, font)
        texts.append(
            Text(
                text=name,
                rect=Rect(int(x), int(y), int(w), int(h)),
                font=font,
                color=color,
            )
        )
    return texts


def _(t):
    out = ''
    for i in t:
        if i.isdigit():
            out += '०१२३४५६७८९'[int(i)]
        else:
            out += i
    return out


class IDCardTemplate(Template):
    """身份证用模板"""
    
    def replace_text(self, engine):
        """
        engine 是faker引擎，如果是key说明不变不用换，否则用engine的key 方法替换
        :param engine: faker(si).profile('key')
        :return:
        """
        name = ''
        for text in self.texts:
            if text.text in ("IMAGE", "image@"):
                continue
            if text.text in ("SIGN", "sign@", "script@"):
                continue
            if text.text.startswith("key@"):
                if engine.locale in ('id',):
                    text.text = text.text.removeprefix('key@')
                # else:
                #     text.text = ""
            elif "@" in text.text:
                label, txt = text.text.split("@")
                if engine.locale == 'ne' and label in ('spnumber', 'spbirth'):
                    continue
                if engine.locale == 'bn' and label == 'name_en':
                    text.text = default_engine.sentence_like(txt, False)
                elif engine.locale in ('HKG', 'zh_CN', 'zh', 'CN', 'MO'):
                    text.text = txt
                else:
                    keep_ascii = engine.locale in (
                        'km', 'ne', 'lo_LA', 'bn', 'si')
                    text.text = engine.sentence_like(txt, exact=True,
                                                     keep_ascii=keep_ascii)
                if label in ('name', 'given_names', 'name_en'):
                    name = text.text
                if label == 'number':
                    number = text.text
                if label == 'birth':
                    birth = text.text
        
        for text in self.texts:
            if text.text in ("SIGN", "sign@", "script@"):
                text.text = name.split()[0] if ' ' in name else name
                if text.font is None:
                    text.font = engine.font("sign")
            if engine.locale == 'ne':
                if text.text.split('@')[0] == 'spnumber':
                    text.text = _(number)
                if text.text.split('@')[0] == 'spbirth':
                    text.text = _(birth)
    
    def render_image_data(self):
        try:
            person_img = rand_person()
        except Exception:
            person_img = Image.new('RGB',(500,500),(0,255,0))
        for text in self.texts:
            if text.text in ("IMAGE", "image@"):
                img = person_img.resize(text.rect.size)
                # image_data['image'].paste(img, text.rect.topleft)
                self.image.paste(img, text.rect.topleft)
                # image_data['mask'].paste(Image.new('RGBA',text.rect.size,(255,255,255,255)),text.rect.topleft)
        return super().render_image_data()
    
    def render_image_data_poison(self):
        
        person_img = rand_person()
        image = self.image.copy()
        text_layer = Image.new('RGB', image.size, (255, 255, 255))
        text_drawer = ImageDraw.Draw(text_layer)
        
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(image)
        mask_draw = ImageDraw.Draw(mask)
        text_list = []
        for text in self.texts:
            if text.text in ("<LTImage>", "IMAGE", "image@"):
                img = person_img.resize(text.rect.size)
                image.paste(img, text.rect.topleft)
                self.image.paste(img, text.rect.topleft)
                continue
            
            if text.text.startswith("key@"):  # 固定位置的文字不重写
                text_box = [text.rect.left, text.rect.top, text.rect.right,
                            text.rect.bottom]
                text_list.append(
                    [text_box, "text@" + text.text.removeprefix("key@")])
                continue
            
            if text.font is None or text.font.lower() in ("b", "i"):
                # """原始模板，没填充的"""
                draw.rectangle(
                    (text.rect.left, text.rect.top, text.rect.right,
                     text.rect.bottom),
                    outline=random_color(),
                    width=2,
                )
                font = ImageFont.truetype(self.default_font, text.rect.height)
            else:
                size = text.rect.height  # - 4
                # 重新居中渲染
                # print(text.font)
                try:
                    font = ImageFont.truetype(text.font, size)
                except Exception as e:
                    print(e)
                    print(text.font)
                # 如果字宽小于框宽或字符串单词数较少
                image = poison_text(image, (text.rect.left, text.rect.top),
                                    text.text, text.color, font, mode='mixed')
                # draw.text((text.rect.left, text.rect.top), text.text,
                #           text.color, font)
                text_drawer.text((text.rect.left, text.rect.top), text.text,
                                 text.color, font)
                mask_draw.text((text.rect.left, text.rect.top), text.text,
                               255, font)
                # mask_draw.rectangle((text.rect.left,text.rect.top,text.rect.right,text.rect.bottom),(255,255,255,255))
            
            text_box = draw.textbbox((text.rect.left, text.rect.top), text.text,
                                     font)
            text_list.append([text_box, "text@" + text.text])
        
        boxes = [tb[0] for tb in text_list]
        label = [tb[1] for tb in text_list]
        points = []
        for box in boxes:
            points.append([box[0], box[1]])
            points.append([box[2], box[1]])
            points.append([box[2], box[3]])
            points.append([box[0], box[3]])
        
        return {
            "image"     : image,
            # cv2.cvtColor(np.array(image, np.uint8),cv2.COLOR_RGB2BGR),
            "boxes"     : boxes,  # box 和 label是一一对应的
            "label"     : label,
            "points"    : points,
            "mask"      : mask,
            'text_layer': text_layer,
            "background": self.image.copy(),
        }
    
    @classmethod
    def from_html(cls, file):
        """从html文件生成模板"""
        path, _ = os.path.splitext(file)
        texts = get_texts_from_photoshop_html(file)
        image = Image.open(path + ".png")
        return cls(image, texts)


class FormTemplate(Template):
    """表格类模板"""
    
    @classmethod
    def from_table(cls, table, **kwargs):
        """从表格字符串生成模板"""
        return table2template(table, **kwargs)
    
    def replace_text(self, engine, translator=None):
        font = engine.font('n')
        tempfont = ImageFont.truetype(font, self.texts[0].rect.height)
        for text in self.texts:
            if not text.text.isdigit():
                tmp = engine.sentence_fontlike(tempfont, text.rect.width)
                text.text = tmp.title() if random.random() < 0.5 else tmp
            # todo modify nums
            text.font = font
    
    def render_image_data(self):
        data = super().render_image_data()
        data['image'] = p2c(data['image'])
        return data


from awesometable.awesometable import (
    H_SYMBOLS,
    V_LINE_PATTERN,
    count_padding,
    replace_chinese_to_dunder,
)
from prettytable.prettytable import _str_block_width


def table2template(
        table,
        xy=None,
        font_size=20,
        bgcolor="white",
        background=None,
        bg_box=None,
        font_path="simfang.ttf",
        line_pad=0,
        line_height=None,
        vrules="ALL",
        hrules="ALL",
        keep_ratio=False,
        debug=False,
        fgcolor="black"):
    """
    将PrettyTable 字符串对象化为模板
    """
    
    assert font_size % 4 == 0
    lines = str(table).splitlines()
    char_width = font_size // 2
    half_char_width = char_width // 2
    if not xy:
        x, y = 0, 0
    else:
        x, y = xy
    w = (len(lines[0]) + 1) * char_width + x * 2  # 图片宽度
    if line_height is None:
        line_height = font_size + line_pad
    
    h = (len(lines)) * line_height + y * 2  # 图片高度
    
    if background is not None and bg_box:
        x1, y1, x2, y2 = bg_box
        w0, h0 = x2 - x1, y2 - y1
        if isinstance(background, str):
            background = Image.open(background)
        elif isinstance(background, np.ndarray):
            background = Image.fromarray(
                cv2.cvtColor(background, cv2.COLOR_BGR2RGB))
        wb, hb = background.size
        if not keep_ratio:
            wn, hn = int(wb * w / w0), int(hb * h / h0)
            background = background.resize((wn, hn))
            x0, y0 = int(x1 * w / w0), int(y1 * h / h0)
        else:
            wn, hn = int(wb * w / w0), int(hb * w / w0)  # 宽度自适应，高度保持比例
            background = background.resize((wn, hn))
            x0, y0 = int(x1 * w / w0), int(y1 * w / w0)
    else:
        background = Image.new("RGB", (w, h), bgcolor)
        x0, y0 = x + char_width, y + char_width
    
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
    
    cell_boxes = set()  # 多行文字的外框是同一个，需要去重
    text_boxes = []  # 文本框
    texts = []
    for lno, line in enumerate(lines):
        v = lno * line_height + y0
        start = half_char_width + x0
        
        cells = re.split(V_LINE_PATTERN, line)[1:-1]
        if not cells:
            # text_box = draw.textbbox((start, v), line, font=font, anchor="lm")
            texts.append(
                Text(
                    text=line,
                    rect=Rect(start, v - char_width, font.getlength(line),
                              font_size),
                )
            )
            continue
        
        for cno, cell in enumerate(cells):
            ll = sum(_str_block_width(c) + 1 for c in cells[:cno]) + 1
            if cell == "" or "═" in cell:
                start += (len(cell) + 1) * char_width
            else:
                box = draw.textbbox((start, v), cell, font=font,
                                    anchor="lm")  # 左中对齐
                if box[1] != box[3]:  # 非空单元内文字框
                    # draw.text((start, v), cell, font=font, fill="black", anchor="lm")
                    lpad, rpad = count_padding(cell)
                    l = box[0] + lpad * char_width
                    striped_cell = cell.strip()
                    if "  " in striped_cell:  # 如果有多个空格分隔
                        lt = l
                        rt = 0
                        for text in re.split("( {2,})", striped_cell):
                            if text.strip():
                                rt = lt + _str_block_width(text) * char_width
                                # text_box = (lt, box[1], rt, box[3])
                                # text_boxes.append([text_box, "text@" + text])
                                texts.append(
                                    Text(
                                        text=text,
                                        rect=Rect(
                                            lt,
                                            v - char_width,
                                            font.getlength(text),
                                            font_size,
                                        ),
                                    )
                                )
                            
                            else:  # 此时text是空格
                                lt = rt + _str_block_width(text) * char_width
                    else:
                        r = box[2] - rpad * char_width
                        
                        texts.append(
                            Text(
                                text=striped_cell,
                                rect=Rect(
                                    l,
                                    v - char_width,
                                    font.getlength(striped_cell),
                                    font_size,
                                ),
                            )
                        )
                
                left = box[0] - half_char_width  # 其实box以及包括了空白长度，此处可以不偏置
                right = box[2] + half_char_width
                start = right + half_char_width
                
                # 处理多行文字
                tt = lno - 1
                bb = lno + 1
                # 原因：_str_block_width 和 [ll]不一样,解决方法，将中文替换为2个字母
                
                while replace_chinese_to_dunder(lines, tt)[ll] not in H_SYMBOLS:
                    tt -= 1
                while replace_chinese_to_dunder(lines, bb)[ll] not in H_SYMBOLS:
                    bb += 1
                cbox = (
                    left, tt * line_height + y0, right, bb * line_height + y0)
                cell_boxes.add(cbox)
    
    # 以下处理标注
    for box in cell_boxes:
        text_boxes.append([box, "cell@"])
        if vrules == "ALL":
            draw.line((box[0], box[1]) + (box[0], box[3]), fill=fgcolor,
                      width=2)
            draw.line((box[2], box[1]) + (box[2], box[3]), fill=fgcolor,
                      width=2)
        if hrules == "ALL":
            draw.line((box[0], box[1]) + (box[2], box[1]), fill=fgcolor,
                      width=2)
            draw.line((box[0], box[3]) + (box[2], box[3]), fill=fgcolor,
                      width=2)
        if hrules == "dot":
            draw.text((box[0], box[1]),
                      '-' * (int((box[2] - box[0]) / font.getlength('-'))),
                      fgcolor, font, anchor='lm')
            draw.text((box[0], box[3]),
                      '-' * (int((box[2] - box[0]) / font.getlength('-'))),
                      fgcolor, font, anchor='lm')
        
        if debug:
            print(box, "@cell")
    
    points = []
    boxes = [tb[0] for tb in text_boxes]  # 单纯的boxes分不清是行列还是表格和文本
    l, t, r, b = boxes[0]  # 求表格四极
    for box in boxes:
        points.append([box[0], box[1]])
        points.append([box[2], box[1]])
        points.append([box[2], box[3]])
        points.append([box[0], box[3]])
        l = min(l, box[0])
        t = min(t, box[1])
        r = max(r, box[2])
        b = max(b, box[3])
    boxes.append([l, t, r, b])
    points.append([l, t])
    points.append([r, t])
    points.append([r, b])
    points.append([l, b])
    
    label = [tb[1] for tb in text_boxes] + ["table@0"]
    
    return FormTemplate(background, texts)


def nolinetable2template(
        table,
        xy=None,
        font_size=20,
        bgcolor="white",
        background=None,
        bg_box=None,
        font_path="simfang.ttf",
        line_pad=0,
        line_height=None,
        logo_path=None,
        watermark=True,
        dot_line=False,
        multiline=False,
        debug=False,
        vrules=None):
    """
    将银行流水单渲染成图片
    """
    assert font_size % 4 == 0
    origin_lines = str(table).splitlines()
    lines = list(filter(lambda x: "<r" not in x, origin_lines))  # 过滤掉标记
    
    char_width = font_size // 2  # 西文字符宽度
    half_char_width = char_width // 2
    
    w = (len(lines[0]) + 1) * char_width  # 图片宽度
    h = (len(lines)) * font_size  # 图片高度
    
    if line_height is None:
        line_height = font_size + line_pad
    
    if background and bg_box:
        x1, y1, x2, y2 = bg_box
        w0, h0 = x2 - x1, y2 - y1
        background = Image.open(background)
        wb, hb = background.size
        wn, hn = int(wb * w / w0), int(hb * h / h0)
        background = background.resize((wn, hn))
        x0, y0 = int(x1 * w / w0), int(y1 * h / h0)
    else:
        background = Image.new("RGB", (w, h), bgcolor)
        x0, y0 = xy or (char_width, char_width)
        if watermark and logo_path:
            try:
                logo = Image.open(logo_path).resize((w // 2, w // 2))
                background.paste(logo, (w // 4, h // 4), mask=logo)
            except FileNotFoundError:
                pass
    
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
    titlesize = font_size + 8
    titlefont = ImageFont.truetype(font_path, titlesize, encoding="utf-8")
    
    boxes = set()  # 多行文字的外框是同一个，需要去重
    text_boxes = []  # 文本框
    is_odd_line = True
    if multiline:
        lines_to_draw = (6, 10)
    else:
        lines_to_draw = (6, 8)
    last = 0
    rno = 0
    max_cols = 0
    
    for lno, line in enumerate(lines):
        v = lno * line_height + y0
        start = half_char_width + x0
        rowleft = x0
        cells = re.split(V_LINE_PATTERN, line)[1:-1]
        
        if lno == 1:  # title
            title = cells[0].strip()
            # draw.text((w // 2, v), title, font=titlefont, fill="black", anchor="mm")
            box = draw.textbbox((w // 2, v), title, font=titlefont, anchor="mm")
            text_boxes.append([box, "text@" + title])
            
            if logo_path:
                try:
                    logo = Image.open(logo_path)
                    xy = (
                        box[0] - logo.size[0],
                        box[1] + titlesize // 2 - logo.size[1] // 2,
                    )
                    background.paste(logo, xy, mask=logo)
                except FileNotFoundError:
                    pass
            if debug:
                draw.rectangle(box, outline="green")
            continue
        
        if lno == 7:
            max_cols = len(cells)
        if lno == 6:
            last = v
        
        if "═" in line:
            if lno in lines_to_draw:  # 用---虚线
                if dot_line and vrules==None:
                    draw.text((0, v), "-" * (2 * len(line) - 2), fill="black")
                else:
                    draw.line((x0, v) + (w - x0, v), fill="black", width=2)
            
            if lno > 6:
                if multiline:
                    if is_odd_line:
                        text_boxes.append(
                            [[x0, last, w - x0, v], "行-row@%d" % rno])
                        is_odd_line = not is_odd_line
                        if debug:
                            draw.rectangle(
                                (x0, last) + (w - x0, v), outline="red", width=2
                            )
                            draw.text((x0, last), "row@%d" % rno, fill="red")
                        rno += 1
                    else:
                        is_odd_line = not is_odd_line
                
                else:
                    text_boxes.append([[x0, last, w - x0, v], "行-row@%d" % rno])
                    if debug:
                        draw.rectangle((x0, last) + (w - x0, v), outline="red",
                                       width=2)
                        draw.text((x0, last), "row@%d" % rno, fill="red")
                    rno += 1
                last = v
            continue
        
        # 以下内容将不会包含'═'
        for cno, cell in enumerate(cells):
            ll = sum(_str_block_width(c) + 1 for c in cells[:cno]) + 1
            if cell == "":  #
                start += char_width
                continue
            if "═" not in cell:
                box = draw.textbbox((start, v), cell, font=font, anchor="lm")
                if box[1] != box[3]:  # 非空单元内文字框
                    # draw.text((start, v), cell, font=font, fill="black", anchor="lm")
                    lpad, rpad = count_padding(cell)
                    l = box[0] + lpad * char_width
                    striped_cell = cell.strip()
                    # 如果有多个空格分隔,例如无线表格
                    if "  " in striped_cell:
                        lt, rt = l, l
                        for text in re.split("( {2,})", striped_cell):
                            if text.strip():
                                rt = lt + _str_block_width(text) * char_width
                                text_box = (lt, box[1], rt, box[3] - 1)
                                if debug:
                                    draw.rectangle(text_box, outline="green")
                                text_boxes.append([text_box, "text@" + text])
                            else:
                                lt = rt + _str_block_width(text) * char_width
                    else:
                        r = box[2] - rpad * char_width
                        text_box = (l, box[1], r, box[3])
                        if debug:
                            draw.rectangle(text_box, outline="green")
                        text_boxes.append([text_box, "text@" + striped_cell])
                
                left = box[0] - half_char_width
                right = box[2] + half_char_width
                start = right + half_char_width
                tt = lno - 1
                bb = lno + 1
                # 原因：_str_block_width 和 [ll]不一样,解决方法，将中文替换为2个字母
                while replace_chinese_to_dunder(lines, tt)[ll] not in H_SYMBOLS:
                    tt -= 1
                while replace_chinese_to_dunder(lines, bb)[ll] not in H_SYMBOLS:
                    bb += 1
                cbox = (
                left, tt * line_height + y0, right, bb * line_height + y0)
                boxes.add(cbox)
                if not is_odd_line and cell.strip():
                    label = "跨行列格-cell@{rno}-{rno},{cno}-{cno}".format(
                        rno=rno - 1, cno=max_cols + cno
                    )
                    if [cbox, label] not in text_boxes:
                        text_boxes.append([cbox, label])
                    if debug:
                        draw.rectangle(cbox, outline="blue", width=3)
                        draw.text((cbox[0], cbox[1]), label, fill="blue")
            else:
                end = start + (len(cell) + 1) * char_width
                left = start - half_char_width
                right = end - half_char_width
                start = end
    
    # 找表宽
    l, t, r, b = list(boxes)[0]
    for box in boxes:
        l = min(l, box[0])
        t = min(t, box[1])
        r = max(r, box[2])
        b = max(b, box[3])
    
    boxes = list(filter(lambda x: not (x[0] == l and x[2] == r), boxes))
    l, t, r, b = boxes[0]
    for box in boxes:
        l = min(l, box[0])
        t = min(t, box[1])
        r = max(r, box[2])
        b = max(b, box[3])
    table = (l, t, r, b)
    
    if debug:
        draw.rectangle([l, t, r, b], outline="purple")
        draw.text((l, t), "table@0", fill="purple", anchor="ld")
    
    cols = []
    for box in boxes:
        if box[3] == b:
            col = [box[0], t, box[2], b]
            cols.append(col)
    
    cols.sort()
    for cno, col in enumerate(cols):
        text_boxes.append([col, "列-column@%d" % cno])
        if vrules == 'all':
            draw.rectangle(col, outline="black")
        if debug:
            draw.rectangle(col, outline="pink")
            draw.text((col[0], col[1]), "col@%d" % cno, fill="pink")
    
    boxes = [tb[0] for tb in text_boxes]  # 单纯的boxes分不清是行列还是表格和文本
    boxes.append([l, t, r, b])
    points = []
    for box in boxes:
        points.append([box[0], box[1]])
        points.append([box[2], box[1]])
        points.append([box[2], box[3]])
        points.append([box[0], box[3]])
    
    label = [tb[1] for tb in text_boxes] + ["表-table@1"]
    
    texts = []
    for lab, box in zip(label, boxes):
        if lab.startswith('text@'):
            texts.append(Text(text=lab.removeprefix('text@'),
                              rect=Rect(box[0], box[1], box[2] - box[0],
                                        box[3] - box[1])))
    
    return FormTemplate(background, texts)
    # return {
    #     "image": cv2.cvtColor(np.array(background, np.uint8), cv2.COLOR_RGB2BGR),
    #     "boxes": boxes,  # box 和 label是一一对应的
    #     "label": label,
    #     "points": points,
    # }


class NewsTemplate(Template):
    """报纸类模板"""
    
    # todo 背景图和字体颜色可能太接近，加一个描边
    @classmethod
    def copy(cls, other):
        return cls(other.image, other.texts)
    
    def replace_text(self, engine, translator=None):
        font_path = engine.font()
        if engine.locale in ('si',):
            font_path = engine.font('b')
        self.image_layer = Image.new('RGBA', self.image.size,
                                     (255, 255, 255, 0))
        for text in self.texts:
            if text.text in ('<LTImage>',):
                # print(text.text)
                w, h = text.rect.size
                img = engine.image(w, h)
                self.image.paste(img, text.rect.topleft)
                self.image_layer.paste(img, text.rect.topleft)
        # print(len(self.texts))
        for text in self.texts:
            w, h = text.rect.size
            if text.text in ("IMAGE", "image@", '<LTImage>'):
                # print(text.text)
                # img = engine.image(w,h)
                # self.image.paste(img,text.rect.topleft)
                continue
            
            font = ImageFont.truetype(font_path, h)
            text.text = engine.sentence_fontlike(font, w)
            text.font = font_path
            text.color = tuple(
                map(lambda x: x // 255 if x > 255 else x, text.color))
    
    def render_image_data(self):
        image_data = super().render_image_data()
        image_data['image_layer'] = self.image_layer
        return image_data


if __name__ == "__main__":
    # 1363/859
    # normal_size = (745, 472)
    # n = 0
    # for i in glob.glob(r"E:/00IT/P/uniform/已标/*/*.json",recursive=True):
    #     t = Template.from_json(i)
    #     print(85.6/54,(85.6,54))
    #     print(745 / 472, (745, 472))
    #     print(t.image.width/t.image.height,t.image.size)
    #
    #     t.image.save(f'{n}.png')
    #     n+=1
    from multifaker import Faker
    
    faker = Faker("si")
    from mlang.unilayout import UniForm
    
    u = UniForm(r"E:\00IT\P\uniform\mlang\config.yaml")
    u.set_faker_engine(Faker("id"))
    for i in u.create():
        print(i)
        # x = table2image(i,font_path=faker.font())['image']
        # cvshow(x)
        t = table2template(i)
        # print(t)
        t.replace_text(engine=faker)
        im = t.render()
        im.show()
        #
    # # rand_person().show()
    # faker = Faker('id')
    # t = IDCardTemplate.from_html('./templates/idcard/id/id.html')
    # t.replace_text(engine=faker)
    # img = t.render()
    # img.show()
