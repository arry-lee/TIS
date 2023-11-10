"""用Photoshop切片功能标注的模板的读取以及渲染"""

import os
import re

from PIL import Image, ImageDraw, ImageFont
from pyrect import Rect

from multifaker import Faker
from .template import Template, Text, random_color
from utils.picsum import rand_person
from utils.poison import poison_text

default_engine = Faker("id")


def get_texts_from_photoshop_html(file):
    """
    从 photoshop 切片导出的 html 中提取texts
    :param file: html文件
    :return: list
    """
    name_pat = re.compile(r"status='(?P<name>.+)'")
    pos_pat = re.compile(
        r'width="(?P<w>\d+)" height="(?P<h>\d+)" border="0" alt="(?P<x>\d+),(?P<y>\d+),(?P<font>.+)"'
    )
    with open(file, "r", encoding="utf-8") as infile:
        text = infile.read()
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
            font = os.path.join(os.path.dirname(file), font)
            color = "#" + color
        else:
            font = os.path.join(os.path.dirname(file), font)
        texts.append(
            Text(
                text=name,
                rect=Rect(int(x), int(y), int(w), int(h)),
                font=font,
                color=color,
            )
        )
    return texts


def _(nums):
    out = ""
    for i in nums:
        if i.isdigit():
            out += "०१२३४५६७८९"[int(i)]
        else:
            out += i
    return out


class IDCardTemplate(Template):
    """身份证用模板"""

    def replace_text(self, engine):
        """
        engine 是faker引擎
        :param engine: faker(si)
        :return:
        """
        name = ""
        for text in self.texts:
            if text.text in ("IMAGE", "image@"):
                continue
            if text.text in ("SIGN", "sign@", "script@"):
                continue
            if text.text.startswith("key@"):
                if engine.locale in ("id",):
                    text.text = text.text.removeprefix("key@")
            elif "@" in text.text:
                label, txt = text.text.split("@")
                if engine.locale == "ne" and label in ("spnumber", "spbirth"):
                    continue
                if engine.locale == "bn" and label == "name_en":
                    text.text = default_engine.sentence_like(txt, False)
                elif engine.locale in ("HKG", "zh_CN", "zh", "CN", "MO"):
                    text.text = txt
                else:
                    keep_ascii = engine.locale in ("km", "ne", "lo_LA", "bn", "si")
                    text.text = engine.sentence_like(
                        txt, exact=True, keep_ascii=keep_ascii
                    )
                if label in ("name", "given_names", "name_en"):
                    name = text.text
                if label == "number":
                    number = text.text
                if label == "birth":
                    birth = text.text

        for text in self.texts:
            if text.text in ("SIGN", "sign@", "script@"):
                text.text = name.split()[0] if " " in name else name
                if text.font is None:
                    text.font = engine.font("sign")
            if engine.locale == "ne":
                if text.text.split("@")[0] == "spnumber":
                    text.text = _(number)
                if text.text.split("@")[0] == "spbirth":
                    text.text = _(birth)

    def render_image_data(self):
        try:
            person_img = rand_person()
        except Exception:
            person_img = Image.new("RGB", (500, 500), (0, 255, 0))
        for text in self.texts:
            if text.text in ("IMAGE", "image@"):
                img = person_img.resize(text.rect.size)
                self.image.paste(img, text.rect.topleft)
        return super().render_image_data()

    def render_image_data_poison(self):
        """使用泊松编辑方法写字"""
        person_img = rand_person()
        image = self.image.copy()
        text_layer = Image.new("RGB", image.size, (255, 255, 255))
        text_drawer = ImageDraw.Draw(text_layer)

        mask = Image.new("L", image.size, 0)
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
                text_box = [
                    text.rect.left,
                    text.rect.top,
                    text.rect.right,
                    text.rect.bottom,
                ]
                text_list.append([text_box, "text@" + text.text.removeprefix("key@")])
                continue

            if text.font is None or text.font.lower() in ("b", "i"):
                # """原始模板，没填充的"""
                draw.rectangle(
                    (text.rect.left, text.rect.top, text.rect.right, text.rect.bottom),
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
                image = poison_text(
                    image,
                    (text.rect.left, text.rect.top),
                    text.text,
                    text.color,
                    font,
                    mode="mixed",
                )
                # draw.text((text.rect.left, text.rect.top), text.text,
                #           text.color, font)
                text_drawer.text(
                    (text.rect.left, text.rect.top), text.text, text.color, font
                )
                mask_draw.text((text.rect.left, text.rect.top), text.text, 255, font)
                # mask_draw.rectangle((text.rect.left,text.rect.top,text.rect.right,text.rect.bottom),(255,255,255,255))

            text_box = draw.textbbox((text.rect.left, text.rect.top), text.text, font)
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
            "image": image,
            # cv2.cvtColor(np.array(image, np.uint8),cv2.COLOR_RGB2BGR),
            "boxes": boxes,  # box 和 label是一一对应的
            "label": label,
            "points": points,
            "mask": mask,
            "text_layer": text_layer,
            "background": self.image.copy(),
        }

    @classmethod
    def from_html(cls, file):
        """从html文件生成模板"""
        path, _ = os.path.splitext(file)
        texts = get_texts_from_photoshop_html(file)
        image = Image.open(path + ".png")
        return cls(image, texts)


class PassportTemplate(IDCardTemplate):
    """护照用模板"""

    def replace_text(self, engine):
        passport = engine.passport()
        for text in self.texts:
            if text.text in ("IMAGE", "image@"):
                continue
            if text.text.startswith("key@"):
                continue
            if "@" in text.text:
                label, txt = text.text.split("@")
                text.text = passport.get(label, "")

    def render_image_data(self):
        """
        渲染模板成图片字典格式,包含标注
        :return:
        """
        self.set_person_image()

        image = self.image.copy()
        text_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
        text_drawer = ImageDraw.Draw(text_layer)

        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(image)
        mask_draw = ImageDraw.Draw(mask)
        text_list = []

        for text in self.texts:
            if text.text in ("IMAGE", "image@"):
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

                def put_text_in_rect(text):
                    """闭包,将text.text拉伸值text.rect的宽度"""
                    width = text.rect.width
                    length = len(text.text)
                    font = ImageFont.truetype(text.font, text.rect.height)
                    delta_x = (width - font.getlength(text.text)) // length

                    ptx = text.rect.left
                    pty = text.rect.top
                    for char in text.text:
                        draw.text((ptx, pty), char, text.color, font)
                        text_drawer.text((ptx, pty), char, text.color, font)
                        mask_draw.text(
                            (ptx, pty), char, 255, font, stroke_fill=255, stroke_width=0
                        )
                        ptx += font.getlength(char) + delta_x

                if len(text.text) == 44:  # 专门针对编号优化
                    put_text_in_rect(text)
                else:
                    font = ImageFont.truetype(text.font, text.rect.height)
                    draw.text(
                        (text.rect.left, text.rect.top), text.text, text.color, font
                    )
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

    def set_person_image(self):
        try:
            person_img = rand_person()
        except Exception:
            person_img = Image.new("RGB", (500, 500), (0, 255, 0))
        for text in self.texts:
            if text.text in ("IMAGE", "image@"):
                img = person_img.resize(text.rect.size)
                self.image.paste(img, text.rect.topleft)
                continue


# for lang in LANG_CODES:
#     p = PassportTemplate.from_html(f"templates/passport/{lang}/{lang}.html")
#     d = p.replace_text(None)
#     print(d)


# class PassportData:
#     """
#     IDN7212228M1701197 << << << << << << << << << < 06
#     """
#
#
# # from faker import Faker
#
# f = Faker("en")
# print(dir(f))
# IDN = {
#     "type": "P",
#     "code": "IDN",
#     "number": "A 2077158",
#     "sex": "L/M",
#     "name": "SUHADI DJAMI ASNAWI",
#     "nationality": "INDONESIA",
#     "birth": "22 DEC 1972",
#     "bp": "SAMPANG",
#     "issue": "19 JAN 2012",
#     "expiry": "19 JAN 2017",
#     "number1": "1A11JC6492-LRW",
#     "authority": "JAKART TIMUR",
#     "number2": "NIKIM 110135813029",
#     "number3": "P<IDNASNAWI<<SUHADI<DJAMI<<<<<<<<<<<<<<<<<<<",
#     "number4": "A2077158<6IDN7212228M1701197<<<<<<<<<<<<<<<<<<<06",
# }
#
# N = f.random_number  # 随机数字
#
#
# def L(n=1):
#     """随机字母"""
#     return "".join(random.sample(string.ascii_uppercase, n))
#
#
# def D():
#     """随机日期"""
#     return f.date_this_decade().strftime("%d %b %Y").upper()
#
#
# def LN():
#     return f.last_name().upper()
#
#
# def FN():
#     return f.first_name().upper()
#
#
# def idn():
#     firstname, midname, lastname = (
#         f.first_name().upper(),
#         f.last_name().upper(),
#         f.last_name().upper(),
#     )
#     sex = random.choice("WF")
#     number = N(7)
#     issue = D()
#     expiry = issue[:-4] + str(int(issue[-4:]) + 5)
#     return {
#         "type": "P",
#         "code": "IDN",
#         "number": f"A {number}",
#         "sex": f"{'L/M' if sex == 'M' else 'V/F'}",
#         "name": f"{firstname} {midname} {lastname}",
#         "nationality": "INDONESIA",
#         "birth": f"{D()}",
#         "bp": f"{f.country().upper()}",
#         "issue": issue,
#         "expiry": expiry,
#         "number1": f"{N(1)}{L()}{N(2)}{L(2)}{N(4)}-{L(3)}",
#         "authority": f"{f.name().upper()}",
#         "number2": f"NIKIM {N(12)}",
#         "number3": f"P<IDN{lastname}<<{firstname}<{midname}".ljust(44,'<'),
#         "number4": f"A{number}<{N(1)}IDN{N(7)}{sex}{N(7)}".ljust(42,'<')+ N(2),
#     }
#
#
# PHL = {
#     "type": "P",
#     "code": "PHL",
#     "number": "P6523327A",
#     "surname": "MIGUEL",
#     "given_names": "EMELYN",
#     "middle_name": "ESTAMA",
#     "birth": "06 NOV 1981",
#     "nationality": "FILIPINO",
#     "sex": "F",
#     "bp": "CAMILING TARLAC",
#     "issue": "22 MAR 2018",
#     "expiry": "21 MAR 2028",
#     "authority": "DFA BACOLOD",
#     "number1": "P<PHLMIGUEL<<EMELYN<<<<<<<<<<<<<<<<<<<<<<<<<",
#     "number2": "P6523327A9PHL8111063F2803216<<<<<<<<<<<<<<02",
# }
#
#
# def phl():
#     surname = LN()
#     given_names = FN()
#     middle_name = LN()
#     sex = random.choice("FM")
#     issue = D()
#     expiry = issue[:-4] + str(int(issue[-4:]) + 10)
#     number = f"P{N(7)}A"
#     # number1 = f"P<PHL{surname}<<{given_names}"
#
#     return {
#         "type": "P",
#         "code": "PHL",
#         "number": number,
#         "surname": surname,
#         "given_names": given_names,
#         "middle_name": middle_name,
#         "birth": D(),
#         "nationality": "FILIPINO",
#         "sex": sex,
#         "bp": f"{f.country()}",
#         "issue": issue,
#         "expiry": expiry,
#         "authority": f"{LN()} {FN()}",
#         "number1": f"P<PHL{surname}<<{given_names}".ljust(44,"<"),
#         "number2": f"{number}{N(1)}PHL{N(7)}{sex}{N(7)}".ljust(42,'<')+ N(2),
#     }
#
#
# def nld():
#     sn = FN()
#     sn1 = LN()
#     gn = FN()
#     gn1 = LN()
#     number = f"{L(5)}{N(4)}"
#     sex = random.choice("FM")
#
#     month = [
#         "JAN/JAN",
#         "FEB/FEB",
#         "MAA/MAR",
#         "APR/APR",
#         "MEI/MAY",
#         "JUN/JUN",
#         "JUL/JUL",
#         "AUG/AUG",
#         "SEP/SEP",
#         "OKT/OCT",
#         "NOV/NOV",
#         "DEC/DEC",
#     ]
#     month_dict = {m[4:]: m[:3] for m in month}
#
#     issue = D().split()
#     issue[1] = month_dict[issue[1]]
#     issue = " ".join(issue)
#     expiry = issue[:-4] + str(int(issue[-4:]) + 10)
#
#     birth = D().split()
#     birth[1] = month_dict[birth[1]]
#
#     return {
#         "type": "P",
#         "code": "NLD",
#         "nationality": "Nederlandse",
#         "number": number,
#         "surname": f"{sn.title()} {sn1.title()}",
#         "surname1": f"e/v {LN().title()}",
#         "given_names": f"{gn.title()} {gn1.title()}",
#         "birth": f"{birth[0]} {birth[1]}",
#         "birth1": f"{birth[2]}",
#         "bp": f"{f.country()}",
#         "sex": f"{'L/M' if sex == 'M' else 'V/F'}",
#         "height": f"1,{random.randint(50, 90)}m",
#         "issue": issue,
#         "expiry": expiry,
#         "authority": f"{f.name()}",
#         "number1": f"P<NLD{sn}<{sn1}<<{gn}<{gn1}".ljust(44,"<"),
#         "number2": f"{number}{N(1)}NLD{N(7)}{sex}{N(16)}".ljust(42,'<')+ N(2),
#     }
#
#
# NLD = {
#     "type": "P",
#     "code": "NLD",
#     "nationality": "Nederlandse",
#     "number": "SPECI2014",
#     "surname": "De Bruijn",
#     "surname1": "e/v Molenaar",
#     "given_names": "Willeke Liselotte",
#     "birth": "10 MAA/MAR",
#     "birth1": "1965",
#     "bp": "Specimen",
#     "sex": "V/F",
#     "height": "1,75m",
#     "issue": "09 MAA/MAR 2014",
#     "expiry": "09 MAA/MAR 2024",
#     "authority": "Burg.van Stad en Dorp",
#     "number1": "P<NLDDE<BRUIJN<<WILLEKE<LISELOTTE<<<<<<<<<<<",
#     "number2": "SPECI20142NLD6503101F2403096999999990<<<<<84",
# }
#
# CZE = {
#     "type": "P",
#     "code": "CZE",
#     "number": "99009054",
#     "surname": "SPECIMEN",
#     "given_names": "VZOR",
#     "nationality": "ČESKÁ REPUBLIKA/CZECH REPUBLIC",
#     "number1": "695622/0612",
#     "birth": "22.06.1969",
#     "sex": "F",
#     "bp": "PRAHA 1",
#     "issue": "29.07.2006",
#     "expiry": "29.07.2016",
#     "authority": "PRAHA 1",
#     "number2": "P<CZESPECIMEN<<VZOR<<<<<<<<<<<<<<<<<<<<<<<<<",
#     "number3": "99009054<4CZE6906229F16072996956220612<<<<<<<<<<<<<<<<<<<<<<<<<74",
# }
#
#
# def cze():
#     issue = f.date_this_decade().strftime("%m.%d.%Y")
#     expiry = issue[:-4] + str(int(issue[-4:]) + 10)
#     sex = random.choice("FM")
#     bp = f"{f.country()} {N(1)}"
#     sn = FN()
#     gn = LN()
#     number = N(8)
#     return {
#         "type": "P",
#         "code": "CZE",
#         "number": number,
#         "surname": sn,
#         "given_names": gn,
#         "nationality": "ČESKÁ REPUBLIKA/CZECH REPUBLIC",
#         "number1": f"{N(6)}/{N(4)}",
#         "birth": f"{f.date_of_birth().strftime('%m.%d.%Y')}",
#         "sex": sex,
#         "bp": bp,
#         "issue": issue,
#         "expiry": expiry,
#         "authority": bp,
#         "number2": f"P<CZE{sn}<<{gn}".ljust(44,'<'),
#         "number3": f"{number}<{N(1)}CZE{N(7)}{sex}{N(16)}".ljust(42,'<')+ N(2),
#     }
#
# GRC = {
#     "type": "P",
#     "code": "ΕΛΛ",
#     "code_en": "/GRC",
#     "number": "AE0000005",
#     "surname": "ΕΛΛΗΝΣ",
#     "surname_en": "ELLINAS",
#     "name": "ΓΕΩΡΓΙΟΣ",
#     "name_en": "GEORGIOS",
#     "nationality": "ΕΛΛΗΝΙΚΗ",
#     "nationality_en": "/ HELLENIG",
#     "sex": "M",
#     "birth": "0 Apr 65",
#     "bp": "ΣΠΑΡΤΗ",
#     "bp1": "GRC",
#     "bp_en": "SPARTI",
#     "issue": "29 Aug 07",
#     "expiry": "28 Aug 12",
#     "authority": "Α.Ε.Α/Δ.Δ-N.P.C.",
#     "height": "1,,82",
#     "number1": "P<GRCELLINAS<<GEORGIOS<<<<<<<<<<<<<<<",
#     "number2": "AE00000057GRC6504049M1208283<<<<<<<<<<<<<<<00",
# }
#
#
# def grc():
#
#     number = f"{L(2)}{N(7)}"
#     birth = f.date_of_birth().strftime("%d %b %Y")
#     issue = f.date_this_decade().strftime("%d %b %Y")
#     expiry = issue[:-4] + str(int(issue[-4:]) + 5)
#     birth = birth[:-4] + birth[-2:]
#     issue = issue[:-4] + issue[-2:]
#     expiry = expiry[:-4] + expiry[-2]
#     sex = random.choice("FM")
#     name_en = LN()
#     surname_en = FN()
#     faker_el = Faker("el_GR")
#     return {
#         "type": "P",
#         "code": "ΕΛΛ",
#         "code_en": "/GRC",
#         "number": number,
#         "surname": faker_el.word().upper(),
#         "surname_en": surname_en,
#         "name": faker_el.word().upper(),
#         "name_en": name_en,
#         "nationality": "ΕΛΛΗΝΙΚΗ",
#         "nationality_en": "/HELLENIG",
#         "sex": sex,
#         "birth": birth,
#         "bp": faker_el.word().upper(),
#         "bp1": "GRC",
#         "bp_en": f"{f.country().upper()}",
#         "issue": issue,
#         "expiry": expiry,
#         "authority": "Α.Ε.Α/Δ.Δ-N.P.C.",
#         "height": f"1,{random.randint(50,90)}",
#         "number1": f"P<GRC{surname_en}<<{name_en}".ljust(44,'<'),
#         "number2": f"{number}{N(1)}GRC{N(7)}{sex}{N(7)}".ljust(42,'<')+ N(2),
#     }
#
#
# BGD = {
#     "type": "P",
#     "code": "BGD",
#     "number": "AG8148412",
#     "surname": "LIMA",
#     "given_names": "TASLIMA AKTER",
#     "number1": "19813090639100765",
#     "nationality": "BANGLADESHI",
#     "birth": "25DEC 1981",
#     "sex": "F",
#     "bp": "DHAKA",
#     "authirity": "DIP/DHAKA",
#     "issue": "12 SEP 2013",
#     "expiry": "11 SEP 2018",
#     "number2": "P<BGDLIMA<<TASLIM<AKTER<<<<<<<<<<<<<<<<<<<<<",
#     "number3": "AG81484126BGD8112255F1809118<<<<<<<<<<<<<02",
# }
#
#
# def bgd():
#     sn = FN()
#     gn1 = LN()
#     gn2 = LN()
#     issue = D()
#     expiry = issue[:-4] + str(int(issue[-4:]) + 5)
#     bp = f.country().upper()
#     sex = random.choice("FM")
#     number = f"{L(2)}{N(7)}"
#     return {
#         "type": "P",
#         "code": "BGD",
#         "number": number,
#         "surname": sn,
#         "given_names": f"{gn1} {gn2}",
#         "number1": N(17),
#         "nationality": "BANGLADESHI",
#         "birth": D(),
#         "sex": sex,
#         "bp": bp,
#         "authirity": f"DIP/{bp}",
#         "issue": issue,
#         "expiry": expiry,
#         "number2": f"P<BGD{sn}<<{gn1}<{gn2}".ljust(44,'<'),
#         "number3": f"{number}{N(1)}BGD{N(7)}{sex}{N(7)}".ljust(42,'<')+ N(2),
#     }
#
#
# NPL = {
#     "type": "P",
#     "code": "NPL",
#     "number": "11331200",
#     "surname": "B K",
#     "given_names": "NIRAJ",
#     "nationality": "NEPALESE",
#     "birth": "13 APR 2000",
#     "number1": "62-01-75-03613",
#     "sex": "M",
#     "bp": "JAJARKOT",
#     "authority": "MOFA,DEPARTMET OF PASSPORT",
#     "issue": "22 FEB 2019",
#     "expiry": "21 FEB 2029",
#     "number2": "P<NPLB<K<<NIRAJ<<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
#     "number3": "11331200<9NPL0004134M290221262017503613<<<28",
# }
#
#
# def npl():
#     number = N(8)
#     sex = random.choice("FM")
#     issue = D()
#     expiry = issue[:-4] + str(int(issue[-4:]) + 10)
#     sn1 = FN()
#     sn2 = FN()
#     gn = LN()
#     return {
#         "type": "P",
#         "code": "NPL",
#         "number": number,
#         "surname": f"{sn1} {sn2}",
#         "given_names": gn,
#         "nationality": "NEPALESE",
#         "birth": D(),
#         "number1": f"{N(2)}-{N(2)}-{N(2)}-{N(5)}",
#         "sex": sex,
#         "bp": f.country().upper(),
#         "authority": "MOFA,DEPARTMET OF PASSPORT",
#         "issue": issue,
#         "expiry": expiry,
#         "number2": f"P<NPL{sn1}<{sn2}<<{gn}".ljust(44,'<'),
#         "number3": f"{number}<{N(1)}NPL{N(7)}{sex}{N(18)}".ljust(42,'<')+ N(2),
#     }
#
#
# LKA = {
#     "type": "PA",
#     "code": "LKA",
#     "number": "N0275917",
#     "surname": "AZEEZ",
#     "given_names": "SEINAMBU",
#     "job": "HOUSE MAID",
#     "nation": "SRI LANKAN",
#     "birth": "28/10/1966",
#     "number1": "668025137V",
#     "sex": "F",
#     "bp": "MUDUR",
#     "authority": "කෝලෝම්බෝ",
#     "issue": "01/12/2004",
#     "expiry": "10/12/2009",
#     "number2": "PALKAAZEEZ<<SEINAMBU<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
#     "number3": "N0275917<4LKA6610285F0912013668025137V<<<<98",
# }
#
#
# def lka():
#     number = f"N{N(7)}"
#     sex = random.choice("FM")
#     birth = f.date_of_birth().strftime("%d/%m/%Y")
#     issue = f.date_this_decade().strftime("%d/%m/%Y")
#     expiry = issue[:-4] + str(int(issue[-4:]) + 10)
#     sn = FN()
#     gn = LN()
#     number1 = f"{N(9)}{L(1)}"
#     return {
#         "type": "PA",
#         "code": "LKA",
#         "number": number,
#         "surname": sn,
#         "given_names": gn,
#         "job": "HOUSE MAID",
#         "nation": "SRI LANKAN",
#         "birth": birth,
#         "number1": number1,
#         "sex": sex,
#         "bp": f.country().upper(),
#         "authority": "කෝලෝම්බෝ",
#         "issue": issue,
#         "expiry": expiry,
#         "number2": f"PALKA{sn}<<{gn}".ljust(44,'<'),
#         "number3": f"{number}<{N(1)}LKA{N(7)}{sex}{N(7)}{number1}".ljust(42,'<')+ N(2),
#     }
#
#
# KHM = {
#     "number": "N0572628",
#     "type": "PN",
#     "code": "KHM",
#     "surname": "SOM ANG",
#     "given_name": "VIBOL",
#     "nationality": "CAMBODIAN",
#     "birth": "06 SEP /SEPT 1986",
#     "bp": "KOMPONG SPEU",
#     "sex": "M",
#     "issue": "01 FEB /FEV 2008",
#     "authority": "MIN PHNOM PENH",
#     "expiry": "01 FEB /FEV 2011",
#     "number1": "PNKHMSON<ANG<<VIBOL<<<<<<<<<<<<<<<<<<<<<<<<<",
#     "number2": "N0572628<5KHM8609063M110201500078294<<<<<<06",
# }
#
#
# def khm():
#     number = f"N{N(7)}"
#     sn1 = FN()
#     sn2 = FN()
#     gn = LN()
#     sex = random.choice("FM")
#     month = [
#         "JAN/JAN",
#         "FEV/FEB",  #
#         "MARS/MAR",
#         "AVR/APR",  #
#         "MEI/MAY",
#         "JUNE/JUN",  #
#         "JULY/JUL",
#         "AUG/AUG",
#         "SEPT/SEP",  #
#         "OCT/OCT",
#         "NOV/NOV",  #
#         "DEC/DEC",
#     ]
#     month_dict = {m[-3:]: m[:-4] for m in month}
#     birth = D().split()
#     birth.insert(2, "/" + month_dict[birth[1]])
#     birth = " ".join(birth)
#     issue = D().split()
#     issue.insert(2, "/" + month_dict[birth[1]])
#     issue = " ".join(issue)
#     expiry = issue[:-4] + str(int(issue[-4:]) + 5)
#     return {
#         "number": number,
#         "type": "PN",
#         "code": "KHM",
#         "surname": f"{sn1} {sn2}",
#         "given_name": f"{gn}",
#         "nationality": "CAMBODIAN",
#         "birth": birth,
#         "bp": f.country().upper(),
#         "sex": sex,
#         "issue": issue,
#         "authority": "MIN PHNOM PENH",
#         "expiry": expiry,
#         "number1": f"PNKHM{sn1}<{sn2}<<{gn}".ljust(44,'<'),
#         "number2": f"{number}<{N(1)}KHM{N(7)}M{N(15)}".ljust(42,'<')+ N(2),
#     }
#
#
# NON = {
#     "issue": "19 May 2017",
#     "expiry": "14 May 2018",
#     "entries": "Multiple",
#     "issue_area": "VIENTIANE",
#     "date": "19 May 2017",
#     "number": "046096924",
#     "type": "C-B1",
#     "remarks": "ກະຊວງ ສາທາລະນະສກ",
#     "kc": "NON",
# }
#
#
# def non():
#     issue = D().title()
#     expiry = issue[:-4] + str(int(issue[-4:]) + 5)
#     return {
#         "issue": issue,
#         "expiry": expiry,
#         "entries": "Multiple",
#         "issue_area": f.country().upper(),
#         "date": f"{D().title()}",
#         "number": N(9),
#         "type": "C-B1",
#         "remarks": "ກະຊວງ ສາທາລະນະສກ",
#         "kc": "NON",
#     }
#
#
# MYS = {
#     "type": "P",
#     "code": "MYS",
#     "number": "A50957608",
#     "name": "MICHELLE YEOH CHOO-KHENG",
#     "nationality": "MALAYSIA",
#     "number1": "130511071234",
#     "birth": "06 AUG 1962",
#     "bp": "IPOH PERAK",
#     "height": "163 CM",
#     "sex": "P-F",
#     "issue": "19 MAY 2018",
#     "expiry": "19 MAY 2023",
#     "authority": "UTC SUNGAI PETANI",
#     "number2": "P<MYSMICHELLE<<YEOH<CHOO<KHENG<<<<<<<<<<<<<<",
#     "number3": "A509576080MYS6208065F230519013051107<<<<<<94",
# }
#
#
# def mys():
#     number = f"A{N(8)}"
#     fn = FN()
#     mn = FN()
#     ln = LN()
#     sex = random.choice("FM")
#     issue = D()
#     expiry = issue[:-4] + str(int(issue[-4:]) + 5)
#
#     return {
#         "type": "P",
#         "code": "MYS",
#         "number": number,
#         "name": f"{fn} {mn} {ln}",
#         "nationality": "MALAYSIA",
#         "number1": f"{N(12)}",
#         "birth": f"{D()}",
#         "bp": f.country().upper(),
#         "height": f"1{random.randint(50,90)} CM",
#         "sex": f"P-{sex}",
#         "issue": issue,
#         "expiry": expiry,
#         "authority": "UTC SUNGAI PETANI",
#         "number2": f"P<MYS{fn}<<{mn}<{ln}".ljust(44,'<'),
#         "number3": f"{number}{N(0)}MYS{N(7)}{sex}{N(15)}".ljust(42,'<')+ N(2),
#     }
