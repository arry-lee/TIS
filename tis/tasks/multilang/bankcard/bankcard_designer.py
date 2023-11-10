"""银行卡设计模块"""
import io
import sys

sys.path.extend(["E:\\00IT\\P\\uniform", "E:\\00IT\\P\\uniform\\utils"])
import json
import os
import random

import cv2
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
from pyrect import Rect

from postprocessor.convert import as_image
from postprocessor.logo import bank_list, get_logo_path

headers = """\
accept: application/json, text/javascript, */*; q=0.01
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cookie: Able-Player={%22preferences%22:{%22prefAltKey%22:1%2C%22prefCtrlKey%22:1%2C%22prefShiftKey%22:0%2C%22prefTranscript%22:0%2C%22prefHighlight%22:1%2C%22prefAutoScrollTranscript%22:1%2C%22prefTabbable%22:0%2C%22prefCaptions%22:1%2C%22prefCaptionsPosition%22:%22below%22%2C%22prefCaptionsFont%22:%22sans%22%2C%22prefCaptionsSize%22:%22100%25%22%2C%22prefCaptionsColor%22:%22white%22%2C%22prefCaptionsBGColor%22:%22black%22%2C%22prefCaptionsOpacity%22:%22100%25%22%2C%22prefDesc%22:0%2C%22prefDescFormat%22:%22video%22%2C%22prefDescPause%22:0%2C%22prefVisibleDesc%22:1%2C%22prefSign%22:0}%2C%22sign%22:{}%2C%22transcript%22:{}}; _dd_s=logs=1&id=615d41f1-01a3-40b7-9b18-67c1e0020ab7&created=1661822880885&expire=1661824283686
referer: https://carddesigner.visa.com/
sec-ch-ua: ".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-origin
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36
x-requested-with: XMLHttpRequest
"""

headers = dict(line.split(": ", 1) for line in headers.splitlines() if line)

s = requests.Session()
s.headers = headers
REGIONS = ["AP", "CAN", "CEMEA", "EUROPE", "LAC", "US"]

basedir = os.path.dirname(__file__)
default_cachedir = os.path.join(basedir, "cache")


def diskcache(cache_dir=None, ext=""):
    """对所有需要联网的json内容进行一个本地的缓存"""
    if cache_dir is None:
        cache_dir = default_cachedir
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)

    def wrapper(func):
        def wrapped(*args, **kwargs):
            cache_key = (
                "_".join([str(a) for a in args] + [str(a) for a in kwargs.values()])
                + ext
            )
            path = os.path.join(cache_dir, cache_key)
            if not os.path.exists(path):
                ret = func(*args, **kwargs)
                with open(path, "w") as fp:
                    json.dump(ret, fp)
            else:
                # print('from cache')
                with open(path, "r") as fp:
                    ret = json.load(fp)
            return ret

        return wrapped

    return wrapper


def open_image(url, cache_dir=None, headers=None):
    """
    使用磁盘缓存的方式读取网络图片
    :param url: 网络url
    :param cache_dir: 磁盘缓存路径
    :return: Image
    """
    if cache_dir is None:
        cache_dir = os.path.join(default_cachedir, "image")
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)

    path = os.path.join(cache_dir, url.rsplit("/", 1)[1])
    try:
        img = Image.open(path)
    except FileNotFoundError:
        response = requests.get(url, headers=headers)
        img = Image.open(io.BytesIO(response.content))
        img.save(path)
    return img


@diskcache(cache_dir=os.path.join(default_cachedir, "json"), ext=".json")
def get_region(region):
    # 选择一个地区
    region_dict = {
        "AP": "0020e94b-60f4-4070-9ecb-45a0ed50ad6a",
        "CAN": "8d602bc8-3216-477f-9ee6-96a5cd033200",
        "CEMEA": "ae077861-faa5-45ab-9398-e64cba37ee5b",
        "EUROPE": "196c3d07-71bf-4454-b03c-2d2c5a03ef18",
        "LAC": "916ff5e3-3e0b-40a8-80f5-ce22c0d671f1",
        "US": "e4af3ae6-9969-47b7-8d3a-1559bbb38969",
    }
    params = {
        "path": f"api/featured/getbyregion?regionid={region_dict[region]}",
        "type": "featured",
    }
    region_url = "https://carddesigner.visa.com/api/gateway/getall"
    region_resp = s.get(region_url, params=params)
    region_json = region_resp.json()

    return region_json


@diskcache(cache_dir=os.path.join(default_cachedir, "json/background"), ext=".json")
def get_background(format_id):
    params = {"path": f"api/background/getall?formatId={format_id}", "type": "region"}
    region_url = "https://carddesigner.visa.com/api/gateway/getall"
    region_resp = s.get(region_url, params=params)
    region_json = region_resp.json()
    return region_json


@diskcache(cache_dir=os.path.join(default_cachedir, "json/elements"), ext=".json")
def get_elements(format_id, product_id):
    params = {
        "path": f"api/element/getall?formatId={format_id}&productId={product_id}",
        "type": "element",
    }
    url = "https://carddesigner.visa.com/api/gateway/getall"
    resp = s.get(url, params=params)
    js = resp.json()
    return js


def download_all_region():
    """提前下载好所有素材"""
    for region in REGIONS:
        for one in get_region(region):
            # print(one)
            get_background(format_id=one["formatId"])
            get_elements(format_id=one["formatId"], product_id=one["productId"])


def collide_any(rect, others):
    """
    矩形碰撞判断
    :param rect: Rect
    :param others: List[Rect]
    :return: bool
    """
    for other in others:
        if rect.collide(other) or other.collide(rect) or rect in other or other in rect:
            return True
    return False


def _(text):
    return "_".join(text.lower().split())


class BadTemplateError(Exception):
    pass


class BankCardDesigner:
    size = (748, 472)
    scale = 2.04

    def __init__(self, image, config=None):
        self.background = as_image(image)
        self.add_round_corner(20)
        if isinstance(config, str):
            self._json = json.load(open(config))
        else:
            self._json = config
        self._rects = []
        self._back_rects = []
        self.elements = {}
        self.back_elements = {}
        self.points = []
        self.labels = []
        self.init_elements()
        self._card_number = None
        self._name = None
        self._legend = ""
        self._logo_name = ""

    @classmethod
    def random_template(cls):
        """随机选择一个地区的模板，初始化实例"""
        products = get_region(random.choice(REGIONS))
        hor = [one for one in products if one["format"] == "Physical Horizontal"]
        product = random.choice(hor)
        image_url = random.choice(get_background(product["formatId"])["image"])[
            "imageFront"
        ]
        elements = get_elements(product["formatId"], product["productId"])
        image = open_image(image_url, headers=headers)
        return cls(image, config=elements)

    def _rand_logo(self):
        bankname = random.choice(bank_list)
        try:
            logo = Image.open(get_logo_path(bankname))
        except FileNotFoundError:
            return self._rand_logo()
        return logo

    def set_bank_logo(self, logo=None, engine=None):
        """
        设置银行 logo
        :param logo: logo None 时随机
        :return: None
        """
        if not logo:
            logo = self._rand_logo()
            try:
                _, pos, (width, height) = self.elements["issuer_logo"]
            except KeyError:
                _, pos, (width, height) = self.back_elements["issuer_logo"]
                face = self.back_elements
            else:
                face = self.elements

            size = logo.width * height // logo.height, height
            logo = logo.resize(size)
            font = ImageFont.truetype(engine.font(), height // 3)
            name = engine.sentence(2)
            w, h = font.getsize(name)
            name_logo = Image.new("RGBA", (w, h + 3), (0, 0, 0, 0))
            draw = ImageDraw.Draw(name_logo)
            draw.text(
                (0, 0),
                name,
                (0, 0, 0, 255),
                font,
                stroke_width=1,
                stroke_fill=(255, 255, 255, 255),
            )

            try:
                _, visa_pos, (vw, wh) = face["visa_brand_mark"]
            except KeyError:
                _pos = pos
                pass
            else:
                if abs(visa_pos[1] - pos[1]) < height:
                    if visa_pos[0] < 748 // 2 and pos[0] < 748 // 2:
                        _pos = 748 - w - 30, pos[1]
                        pos = 748 - logo.width - 30, pos[1]
                    elif visa_pos[0] > 748 // 2 and pos[0] > 748 // 2:
                        _pos = 30, pos[1]
                    else:
                        _pos = pos
                else:
                    _pos = pos
            face["issuer_logo"] = logo, pos, (width, height)
            face["logo_name"] = name_logo, (_pos[0], _pos[1] + height), (w, h)
            self._logo_name = name

    def set_card_number(self, number=None):
        """
        设置卡号
        :param number:
        :return:
        """
        if not number:
            number = " ".join([str(random.randint(1000, 9999)) for _ in range(4)])
        self._card_number = number
        try:
            img, pos, (w, h) = self.elements["account_number"]
        except KeyError:
            img, pos, (w, h) = self.back_elements["account_number"]
            face = self.back_elements
        else:
            face = self.elements
        if w > h:
            number_image = self.gen_card_number_image(number, img)
            face["account_number"] = number_image, pos, (w, h)
            # self.set_attr("account_number", number_image)
        else:
            raise BadTemplateError(f"cardnumber {w}<{h}")

    def set_signature(self, name, font, color=(0, 0, 0, 255)):
        try:
            img, pos, size = self.elements["signature_panel"]
        except KeyError:
            img, pos, size = self.back_elements["signature_panel"]
            face = self.back_elements
        else:
            face = self.elements
        signature = self.gen_text_image(name, size, font, color)
        fit_size = signature.width * size[1] // signature.height, int(size[1] * 0.8)
        signature = signature.resize(fit_size)

        img.paste(signature, (0, 0), mask=signature)
        face["signature"] = img, pos, size
        self._name = name

    def set_legend(self, legend, font="arial.ttf", color=(200, 200, 200, 255)):
        # legend = f"Visa Int./{legend}, Licensed User"
        try:
            img, pos, size = self.elements["legend"]
        except KeyError:
            img, pos, size = self.back_elements["legend"]
            face = self.back_elements
        else:
            face = self.elements
        img = self.gen_text_image(legend, size, font, color)
        face["legend"] = img, pos, img.size
        self._legend = legend

    def set_cardholder_name(self, name, font="arial.ttf", color=(200, 200, 200, 255)):
        """设置持有者姓名"""
        try:
            img, pos, size = self.elements["cardholder_name"]
        except KeyError:
            img, pos, size = self.back_elements["cardholder_name"]
            face = self.back_elements
        else:
            face = self.elements
        img = self.gen_text_image(name, size, font, color)
        face["cardholder_name"] = img, pos, img.size

    @staticmethod
    def gen_text_image(text, size, font_path="arial.ttf", color=(200, 200, 200, 255)):
        font = ImageFont.truetype(font_path, int(size[1] * 0.8))
        img = Image.new("RGBA", font.getsize(text))
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), text, color, font)
        return img

    def set_background(self, image):
        self.background = image
        self.add_round_corner(20)

    def add_round_corner(self, radius=20):
        mask = Image.new("L", self.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0) + self.size, radius, fill=255)
        self.background.putalpha(mask)

    @property
    def front(self):
        img = self.background.copy()
        for image, (x, y), _ in self.elements.values():
            img.paste(image, (x, y), mask=image)
        return img

    @property
    def back(self):
        img = self.background.copy()
        for image, (x, y), _ in self.back_elements.values():
            img.paste(image, (x, y), mask=image)
        return img

    def get_data(self, face):
        """转为通用格式"""
        points = []
        labels = []
        if face == "back":
            elements = self.back_elements
            image = cv2.cvtColor(np.asarray(self.back, np.uint8), cv2.COLOR_RGBA2BGRA)
        else:
            elements = self.elements
            image = cv2.cvtColor(np.asarray(self.front, np.uint8), cv2.COLOR_RGBA2BGRA)
        for key, value in elements.items():
            _, (x, y), (w, h) = value
            points.append([x, y])
            points.append([x + w, y])
            points.append([x + w, y + h])
            points.append([x, y + h])
            if key == "account_number":
                label = "account_number@" + self._card_number
            elif key == "cardholder_name":
                label = "cardholder_name@" + self._name
            elif key == "legend":
                label = "legend@" + self._legend
            elif key == "signature_panel":
                label = "signature_panel@" + self._name
            elif key == "logo_name":
                label = "logo_name@" + self._logo_name
            else:
                label = key + "@"
            labels.append(label)
        back_data = {
            "image": image,
            "points": points,
            "label": labels,
        }
        return back_data

    def show(self):
        self.front.show()
        self.back.show()

    def init_elements(self):
        self._rects = []
        self._back_rects = []
        for i in self._json:
            self.set_element(i)
        self._rects = []
        self._back_rects = []

    def set_attr(self, key, value):
        """
        设置属性
        """
        if key not in self.elements:
            raise AttributeError(f"No attribute {key}")

        _, pos, size = self.elements[key]
        image = as_image(value).resize(size)
        self.elements[key] = image, pos, size

    def set_element(self, element):
        """
        设置银行卡的某个元素
        :param element: 元素
        :return: None
        """
        image_url, (x, y, w, h), face = self.parse_element(element)
        x = int(self.scale * x)
        y = int(self.scale * y)
        w = int(self.scale * w)
        h = int(self.scale * h)
        rect = Rect(x, y, w, h)
        image = open_image(image_url, headers=headers).convert("RGBA")
        image = image.resize((w, h))
        # 如果没碰撞
        if face == "front":
            if not collide_any(rect, self._rects):
                self._rects.append(rect)
                self.elements[_(element["name"])] = image, (x, y), (w, h)

            else:
                self.set_element(element)
        else:
            if not collide_any(rect, self._back_rects):
                self._back_rects.append(rect)
                self.back_elements[_(element["name"])] = image, (x, y), (w, h)
            else:
                # 碰撞重试 Todo:可以优化以免碰撞很多次
                self.set_element(element)

    @staticmethod
    def parse_element(element, color=None):
        """解析每个元素"""
        if not color:
            color = random.choice(["silver", "gold"])

        face = "front"

        image_url = element["image"]
        rect = -100, -100, 10, 10
        props = element["props"]
        if props["color"]:
            image_url = BankCardDesigner._choose_color(props, color)

        if props["position"]:
            rect, face = BankCardDesigner._choose_position(props)
        if props["pin"]:
            pin = random.choice(props["pin"])
            image_url = pin["image"]
            if pin["color"]:
                color = random.choice(pin["color"])
                image_url = color["image"]
        if props["shape"]:
            shape = random.choice(props["shape"])
            image_url = shape["image"]
        if props.get("process", []):
            process = random.choice(props["process"])
            image_url = process["image"]
            if process["color"]:
                image_url = BankCardDesigner._choose_color(process, color)

            if process["position"]:
                rect, face = BankCardDesigner._choose_position(process)

        return image_url, rect, face

    @staticmethod
    def _choose_color(props, color):
        image_url = None
        for clr in props["color"]:
            if clr["name"].lower() == color.lower():
                image_url = clr["image"]
                break
        if not image_url:
            image_url = random.choice(props["color"])["image"]
        return image_url

    @staticmethod
    def _choose_position(node):
        front = [i for i in node["position"] if i["card"] == "front"]
        back = [i for i in node["position"] if i["card"] == "back"]
        if not back:
            face = "front"
        if not front:
            face = "back"
        if back and front:
            face = random.choice(["front", "back"])
        if face == "front":
            style = random.choice(random.choice(front)["style"])
        else:
            style = random.choice(random.choice(back)["style"])
        rect = (
            int(style["x"]),
            int(style["y"]),
            int(style["w"]),
            int(style["h"]),
        )
        return rect, face

    @staticmethod
    def gen_card_number_image(number, image=None, style="gold"):
        """
        生成银行卡号图片
        :param number: str 银行卡号字符串,16位,每4位一个空格
        :param style: 'gold' or 'silver'
        :return:
        """

        if image is None:
            image = Image.open(
                os.path.join(
                    default_cachedir, f"image/emboss-{style}-20191125232130200.png"
                )
            )
            oldsize = image.size
        else:
            size = Image.open(
                os.path.join(
                    default_cachedir, f"image/emboss-{style}-20191125232130200.png"
                )
            ).size

            hid = size[1]
            oldsize = image.size
            # 缩放到size[0],以宽为标准缩放
            image = image.resize((size[0], int(oldsize[1] * (size[0] / oldsize[0]))))
            # print(image.size)
            # print(image.height, size[1])
            if image.height <= size[1]:  # 比例相同
                bottom_half = None
            else:
                bottom_half = image.crop((0, hid) + (size[0], image.height))
        nums = "4000 1234 5678 9010"
        pieces = []
        wid = 47
        # hid = image.height
        # print(wid)
        for i in range(0, image.width, wid):
            p = image.crop((i, 0) + (i + wid, hid))
            pieces.append(p)
        font_map = {}
        for num, p in zip(nums, pieces):
            if num not in font_map:
                font_map[num] = p

        out = Image.new("RGBA", image.size)
        for n, i in zip(number, range(0, image.width, wid)):
            out.paste(font_map[n], (i, 0) + (i + wid, hid), mask=font_map[n])
        if bottom_half:
            out.paste(bottom_half, (0, hid))
        return out.resize(oldsize)
