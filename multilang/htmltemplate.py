"""用Photoshop切片功能标注的模板的读取以及渲染"""
import os
import re

from PIL import Image, ImageDraw, ImageFont
from pyrect import Rect

from multilang.template import Template, Text, random_color
from utils.picsum import rand_person
from utils.poison import poison_text
from multifaker import Faker

default_engine = Faker('id')

def get_texts_from_photoshop_html(file):
    """
    从 photoshop 切片导出的 html 中提取texts
    :param file: html文件
    :return: list
    """
    path = os.path.dirname(file)
    name_pat = re.compile(
        r"status='(?P<name>.+)'"
    )
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
            person_img = Image.new('RGB', (500, 500), (0, 255, 0))
        for text in self.texts:
            if text.text in ("IMAGE", "image@"):
                img = person_img.resize(text.rect.size)
                self.image.paste(img, text.rect.topleft)
        return super().render_image_data()
    
    def render_image_data_poison(self):
        """使用泊松编辑方法写字"""
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
