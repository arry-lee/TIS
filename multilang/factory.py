"""
图片工厂
职责：生成各类图片
命令：python factory.py -l si -m bankcard -o outdir -n 1000
"""
import os
import random
import sys
from itertools import cycle

import cv2
import numpy as np
from PIL import (
    Image,
    ImageChops,
    ImageColor,
    ImageDraw,
    ImageFilter,
    ImageFont,
    ImageOps,
)
from pyrect import Rect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

sys.path.append(PROJECT_DIR)
# pylint: disable=wrong-import-position ungrouped-imports
from multilang.bankcard import BadTemplateError, BankCardDesigner
from multilang.filters import iglob

from general_table.bank_data_generator import (
    bank_detail_generator,
    bank_table_generator,
)
from multilang.formtemplate import FormTemplate, nolinetable2template
from multilang.htmltemplate import IDCardTemplate, PassportTemplate
from multilang.template import Template, Text
from multilang.unilayout import UniForm
from postprocessor.convert import c2p
from postprocessor.displace import displace
from postprocessor.harmonizer import harmonize
from postprocessor.foreground import barcode_image, qrcode_image
from postprocessor.rand import (
    random_source, random_displace,
)
from postprocessor.shadow import add_shader
from postprocessor.label import save_and_log

from utils.maxrect import max_left
from utils.picsum import rand_logo
from generator import BaseGenerator
from generator.register import IMAGE_GENERATOR_REGISTRY

DISPLACE_PAPER = os.path.join(PROJECT_DIR, "postprocessor/displace/paper")


@IMAGE_GENERATOR_REGISTRY.register(key='bankcard')
class BankCardGenerator(BaseGenerator):
    """银行卡生成器
    生成器的属性只有一个名字
    只有一个run接口，该接口只有一个必须参数lang，每次调用生成一个图片
    """
    
    def load_template(self, **kwargs):
        temp = BankCardDesigner.random_template()
        try:
            temp.set_card_number()  # 去掉非长条形的数字
        except BadTemplateError:
            return self.load_template(**kwargs)
        return temp
    
    def render_template(self, template, engine):
        template.add_round_corner()
        template.set_bank_logo(engine=engine)
        number = " ".join([str(random.randint(1000, 9999)) for _ in range(4)])
        template.set_card_number(number)
        name = engine.sentence(2)
        template.set_cardholder_name(name, engine.font())
        legend = engine.sentence(4)
        template.set_legend(legend, engine.font())
        template.set_signature(name, engine.font())
        face = random.choice(["back", "front"])
        template.add_round_corner()
        return template.get_data(face)


class TemplateGenerator(BaseGenerator):
    """
    模板生成器
    单一职责是渲染一个模板并生成
    """
    templates_basedir = os.path.join(BASE_DIR, "templates")
    
    def __init__(self, name):
        super().__init__(name)
        self.templates_dir = os.path.join(self.templates_basedir, name)
        self._templates = cycle(iglob(self.templates_dir, ".tpl"))
    
    def load_template(self, **kwargs):
        """加载模板钩子可重写"""
        template_path = next(self._templates)
        template = Template.load(template_path)
        template.path = template_path
        return template
    
    def render_template(self, template, engine):
        """
        渲染模板
        :param template: 模板
        :param engine: 模板渲染引擎
        :return:
        """
        template.replace_text(engine=engine)
        image_data = template.render_image_data()
        image_data["template"] = template
        return image_data
    
    @staticmethod
    def test_template(image_data, **kwargs):
        """保存测试数据,文件与模板同名,用于人工筛选模板"""
        fname = os.path.basename(image_data["template"].path).split(".")[0]
        product_dir = kwargs.get("product_dir")
        save_and_log(image_data, fname, product_dir)


@IMAGE_GENERATOR_REGISTRY.register(key='idcard')
class IDCardGenerator(TemplateGenerator):
    """身份证生成器"""
    
    def load_template(self, **kwargs):
        """
        身份证模板的加载与语言有关
        :param lang: 语言
        :return:
        """
        lang = kwargs.get("lang")
        template_dir = os.path.join(self.templates_dir, lang)
        template_file = os.path.join(template_dir, f"{lang}.html")
        template = IDCardTemplate.from_html(template_file)
        return template
    
    def preprocess(self, template):
        """增加圆角的预处理"""
        template.add_round_corner()
    
    # def render_template(self, template, engine):
    #     """
    #     渲染模板
    #     :param template: 模板
    #     :param engine: 模板渲染引擎
    #     :return:
    #     """
    #     template.replace_text(engine=engine)
    #     image_data = template.render_image_data()  # 采用泊松编辑
    #     return image_data
    
    def postprocess(self, image_data, **kwargs):
        # fname = kwargs.get("fname")
        # product_dir = kwargs.get("product_dir")
        # _save_and_log(image_data, fname + "_poisson", product_dir)
        #
        image_data = self.postprocess_simple(image_data)
        # _save_and_log(image_data, fname + "_simple", product_dir)
        
        image_data = self.postprocess_harmonizer(image_data)
        # _save_and_log(image_data, fname + "_harmonized", product_dir)
        return image_data
    
    @staticmethod
    def postprocess_simple(image_data):
        """文字后处理方法
        1. 泊松融合
        2. 深度学习方法融合
        3. 简单融合
        """
        text_layer = image_data["text_layer"]
        mask = image_data["mask"]
        obg = image_data["background"].convert("RGB")
        # 随机改变透明度，使得像素值不单调
        newmask = mask.point(
            lambda x: x - random.randint(0, 50) if x > 200 else x)
        obg.paste(text_layer, mask=newmask)  # 融合
        size = obg.size
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0) + size, 40, fill=255)
        obg.putalpha(mask)
        
        image_data["image"] = obg
        del image_data["background"]
        del image_data["text_layer"]
        return image_data
    
    # @staticmethod
    def postprocess_harmonizer(self, image_data):
        """文字后处理方法
        1. 泊松融合
        2. 深度学习方法融合
        3. 简单融合

        """
        mask = image_data["mask"]  #
        comp = image_data["image"].convert("RGB")
        res = harmonize(comp, mask)
        size = res.size
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        if self.name == 'idcard':
            draw.rounded_rectangle((0, 0) + size, 40, fill=255)
        else:
            draw.rounded_rectangle((0, 0) + size, 4, fill=255)
        res.putalpha(mask)
        
        image_data["image"] = res
        return image_data


@IMAGE_GENERATOR_REGISTRY.register(key='passport')
class PassportGenerator(IDCardGenerator):
    """护照生成器"""
    
    def load_template(self, **kwargs):
        """
        护照模板的加载与语言有关
        :param lang: 语言
        :return:
        """
        lang = kwargs.get("lang")
        template_dir = os.path.join(self.templates_dir, lang)
        template_file = os.path.join(template_dir, f"{lang}.html")
        template = PassportTemplate.from_html(template_file)
        return template
    
    def preprocess(self, template):
        template.add_round_corner(2)


@IMAGE_GENERATOR_REGISTRY.register(key='newspaper')
class PaperGenerator(TemplateGenerator):
    """报纸杂志类的生成器"""
    
    def preprocess(self, template):
        template.set_background("white")
        template.adjust_texts()  # 移除重叠
    
    def render_template(self, template: Template, engine):
        font_path = engine.font()
        if engine.locale in ("si",):
            font_path = engine.font("b")
        image_layer = Image.new("RGBA", template.image.size, (255, 255, 255, 0))
        for text in template.texts:
            if text.text in ("<LTImage>",):
                width, height = text.rect.size
                try:
                    img = engine.image(width, height)
                except IndexError:
                    img = Image.new('RGB', (width, height), 'white')
                template.image.paste(img, text.rect.topleft)
                image_layer.paste(img, text.rect.topleft)
        
        for text in template.texts:
            width, height = text.rect.size
            if text.text in ("IMAGE", "image@", "<LTImage>"):
                continue
            
            font = ImageFont.truetype(font_path, height)
            text.text = engine.sentence_fontlike(font, width)
            text.font = font_path
            text.color = tuple(
                map(lambda x: x // 255 if x > 255 else x, text.color))
        image_data = template.render_image_data()
        image_data["image_layer"] = image_layer
        return image_data
    
    def postprocess(self, image_data, **kwargs):
        text_layer = image_data["text_layer"]
        image_layer = image_data["image_layer"]
        mask = image_layer.getchannel("A")
        image_layer.paste(text_layer, mask=text_layer)
        # 置换滤镜操作
        # 注释掉的代码用于测试哪些纹理是好的
        # source_dir = r"E:\00IT\P\uniform\postprocessor\displace\paper"
        # for i in tqdm(os.listdir(source_dir)):
        #     texture = os.path.join(source_dir, i)
        #     img = displace(image_layer, texture,ratio = 2)
        #     cv2.imwrite(texture+'.jpg',img)
        comp = random_displace(image_layer, ratio=2)
        # 和谐报纸上的图片显得不那么突兀
        comp = comp.convert("RGB")
        img = harmonize(comp, mask)
        image_data["image"] = cv2.cvtColor(np.asarray(img, np.uint8),
                                           cv2.COLOR_RGB2BGR)
        return image_data


@IMAGE_GENERATOR_REGISTRY.register(key='magazine')
class MagazineGenerator(PaperGenerator):
    """杂志生成器"""


@IMAGE_GENERATOR_REGISTRY.register(key='book')
class BookGenerator(PaperGenerator):
    """书籍生成器"""


@IMAGE_GENERATOR_REGISTRY.register(key='menu')
class MenuGenerator(TemplateGenerator):
    """菜单生成器"""
    
    def preprocess(self, template):
        """
        替换图片多样性
        背景叠加一个实物图片
        优化了 去除碰撞框
        """
        for text in template.texts:
            if text.text == "<LTImage>" and (
                    text.rect.width < template.image.width / 2
                    or text.rect.height < template.image.height / 2
            ):
                path = random_source(
                    os.path.join(self.templates_dir, "images/"))
                try:
                    _im = ImageOps.fit(
                        Image.open(path), text.rect.size
                    )  # .resize(text.rect.size).filter(ImageFilter.GaussianBlur(4))
                except ValueError:
                    pass
                else:
                    template.image.paste(_im, text.rect.topleft)
        path = random_source(os.path.join(self.templates_dir, "images/"))
        obg = template.image
        img = (
            ImageOps.fit(Image.open(path), obg.size)
                .convert("RGB")
                .filter(ImageFilter.GaussianBlur(5))
        )
        obg = ImageChops.blend(obg, img, 0.4)
        template.set_background(obg)
        template.adjust_texts()
    
    def postprocess(self, image_data, **kwargs):
        # text_layer = image_data["text_layer"]
        # bg = image_data["background"]
        # paper = random_source(r"E:\00IT\P\uniform\postprocessor\displace\paper")
        # nbg = add_shader(bg, paper)
        # mask = displace(text_layer, paper, 2, mask_only=True)
        # nbg = c2p(nbg)
        # nbg.paste(mask, mask=mask)
        # image_data["image"] = nbg  # .convert('RGBA')
        del image_data["mask"]
        return image_data


@IMAGE_GENERATOR_REGISTRY.register(key='coupon')
class CouponGenerator(TemplateGenerator):
    """优惠券生成器"""
    
    def postprocess(self, image_data, **kwargs):
        text_layer = image_data["text_layer"]
        paper = random_source(DISPLACE_PAPER)
        nbg = add_shader(image_data["background"], paper)
        mask = displace(text_layer, paper, 2, mask_only=True)
        nbg = c2p(nbg)
        nbg.paste(mask, mask=mask)
        image_data["image"] = nbg
        return image_data


@IMAGE_GENERATOR_REGISTRY.register(key='businesscard')
class BusinessCardGenerator(TemplateGenerator):
    """名片生成器，采用模板方法"""


@IMAGE_GENERATOR_REGISTRY.register(key='vipcard')
class VIPCardGenerator(BusinessCardGenerator):
    """VIP会员卡，复用名片模板，在文字层空白处加上 VIP 元素"""
    
    def __init__(self, name="vipcard"):
        super().__init__("businesscard")
        self.templates_dir = os.path.join(self.templates_basedir, name)
    
    def preprocess(self, template: Template):
        vip_sign = Image.open(
            random_source(os.path.join(self.templates_dir, "vip")))
        template.adjust_texts()
        
        rects = [text.rect for text in template.texts if
                 text.text != "<LTImage>"]
        rect = max_left(rects)
        hmax = max(r.height for r in rects)
        height = min(2 * hmax, rect.height)
        vip_sign = vip_sign.resize(
            (vip_sign.width * height // vip_sign.height, height))
        
        template.image.paste(vip_sign, rect.topleft, mask=vip_sign)
        template.add_round_corner(40)


@IMAGE_GENERATOR_REGISTRY.register(key='form')
class FormGenerator(TemplateGenerator):
    """表格生成器"""
    
    colors = [c for c in ImageColor.colormap if c != "black"]
    
    def __init__(self, name):
        super().__init__(name)
        if name != 'noline':
            self.config_file = os.path.join(self.templates_dir, "config.yaml")
            self.table_generator = UniForm(self.config_file)
    
    def load_template(self, **kwargs):
        table = next(self.table_generator.create())
        # 背景景随机有名色，前景颜色加深
        bg_color = ImageColor.getrgb(random.choice(self.colors))
        fg_color = bg_color[0] // 10, bg_color[1] // 10, bg_color[2] // 10
        border = random.choice(["double", "bold", None])
        vrules = random.choice(["ALL"])
        hrules = random.choice(["ALL", "-"])
        line_width = random.randint(1, 3)
        template = FormTemplate.from_table(
            table,
            xy=(random.randint(50, 80), random.randint(50, 80)),
            font_size=random.choice([20, 24, 28, 32]),
            line_pad=random.randint(-2, 5),
            line_width=line_width,
            bgcolor=bg_color,
            fgcolor=fg_color,
            vrules=vrules,
            hrules=hrules,
            border=border,
        )
        for text in template.texts:
            text.color = fg_color
        return template
    
    def postprocess(self, image_data, **kwargs):
        text_layer = image_data["text_layer"]
        obg = image_data["background"]
        paper = random_source(DISPLACE_PAPER)
        nbg = add_shader(obg, paper)
        mask = displace(text_layer, paper, 2, mask_only=True)
        nbg = c2p(nbg)
        nbg.paste(mask, mask=mask)
        image_data["image"] = nbg
        del image_data["mask"]
        return image_data


@IMAGE_GENERATOR_REGISTRY.register(key='noline')
class NoLineFormGenerator(FormGenerator):
    """无线表格生成"""
    
    def load_template(self, **kwargs):
        data = bank_detail_generator.create()[0]
        align = random.choice("lcr")
        table, multi = bank_table_generator(data, align=align)
        # white_val = random.randint(230, 255)
        bg_color = ImageColor.getrgb(random.choice(self.colors))
        fg_color = bg_color[0] // 10, bg_color[1] // 10, bg_color[2] // 10
        tmp = nolinetable2template(
            table,
            bgcolor=bg_color,
            line_pad=-2,
            watermark=False,
            dot_line=random.choice((True, False)),
            multiline=multi,
            vrules=random.choice(("all", None)),
            fgcolor=fg_color,
        )
        return tmp


@IMAGE_GENERATOR_REGISTRY.register(key='waybill')
class WaybillGenerator(FormGenerator):
    """货运单生成器
    复用通用表格生成器
    配置文件在 ./templates/waybill/config.yaml
    """
    
    def preprocess(self, template):
        """加标题"""


@IMAGE_GENERATOR_REGISTRY.register(key='express')
class ExpressGenerator(FormGenerator):
    """快递单生成器
    复用通用表格生成器
    配置文件在 ./templates/express/config.yaml
    """
    
    def load_template(self, **kwargs):
        table = next(self.table_generator.create(10))
        # 背景景随机有名色，前景颜色加深
        white = random.randint(230, 255)
        black = random.randint(0, 30)
        bg_color = (white, white, white)
        fg_color = (black, black, black)
        # border = random.choice(["double", "bold", None])
        vrules = random.choice(["ALL"])
        hrules = random.choice(["ALL", "-"])
        cell_color = random.choice(self.colors)
        out_color = ImageColor.getrgb(random.choice(self.colors))
        title_color = tuple(255 - o for o in out_color)
        template = FormTemplate.from_table(
            table, xy=(100, 120), bgcolor=bg_color, fgcolor=fg_color,
            border='fill',
            vrules=vrules, hrules=hrules, outcolor=out_color,
            cellcolor=cell_color,
        )
        for text in template.texts:
            if text.text == '<TITLE>':
                text.color = title_color
        # color = random.choice([fg_color, "red", "blue"])
        # i = 0
        # for text in template.texts:
        #     if text.text == '<TITLE>':
        #         i+=1
        #         text.text =
        
        return template
    
    def preprocess(self, template):
        """加条形码"""
        qrcode_img = qrcode_image(template)
        height = 80
        qrcode_img = qrcode_img.resize((height, height))
        pty = 10  # random.choice([10, template.image.height - 90])
        template.image.paste(
            qrcode_img,
            (template.image.width - 160, pty),
            mask=qrcode_img.convert("L").point(lambda x: 255 - x),
        )
        
        try:
            logo = rand_logo()
        except IndexError:
            pass
        else:
            logo = logo.resize((height, height))
            template.image.paste(
                logo,
                (100, pty),
                mask=logo,
            )
        
        template.texts.append(
            Text(rect=Rect(200, pty, template.image.width // 4 - 200, 80)))
        template.texts.append(Text(rect=Rect(100, template.image.height - 100,
                                             template.image.width // 2, 20)))
        template.texts.append(Text(rect=Rect(100, template.image.height - 80,
                                             template.image.width // 4, 20)))
        
        num = "".join([str(random.randint(0, 9)) for i in range(12)])
        bar_img = barcode_image(num)
        bar_img = bar_img.resize((height * 520 // 200, height)).convert("RGB")
        template.image.paste(
            bar_img,
            (template.image.width - 200 - bar_img.width, pty),
            mask=bar_img.convert("L").point(lambda x: 255 - x),
        )
    
    def postprocess(self, image_data, **kwargs):
        text_layer = image_data["text_layer"]
        background = image_data["image"]
        paper = random_source(DISPLACE_PAPER)
        nbg = add_shader(background, paper)
        mask = displace(text_layer, paper, 2, mask_only=True)
        nbg = c2p(nbg)
        nbg.paste(mask, mask=mask)
        image_data["image"] = nbg
        del image_data["mask"]
        return image_data


@IMAGE_GENERATOR_REGISTRY.register(key='receipt')
class ReceiptGenerator(FormGenerator):
    """收银条生成器
    复用通用表格生成器
    配置文件在 ./tempaltes/receipt/config.yaml
    """
    
    def load_template(self, **kwargs):
        table = next(self.table_generator.create(100))
        template = FormTemplate.from_table(
            table, xy=(40, 80), vrules=None, hrules="dot"
        )
        return template
    
    def preprocess(self, template):
        template.adjust_texts()
    
    # def postprocess(self, image_data, **kwargs):
    #     # image_data = super().postprocess(image_data, **kwargs)
    #     # if random.random() < 0.5:
    #     #     h = image_data["image"].shape[0]
    #     #     pos = random.randint(h - 80, h - 40)
    #     #     return keepdata(tear_image_alpha)(image_data, pos, gap=20,
    #     #                                       slope=0.02)
    #     return image_data


"""
  if name in ("bankcard", "idcard", "vipcard", "businesscard"):  # 样机指定
            self._post_processors = [
                {
                    "func": partial(
                        random_mockup, mockup_dir="card", offset=15, crop=True
                    ),
                    "name": "mockup",
                },
            ]
        if name in ("coupons",):  # 样机指定
            self._post_processors = [
                {
                    "func": keepdata(
                        partial(
                            distortion2,
                            peak=random.randint(1, 4),
                            period=random.choice([0.5, 0.75, 1, 1.5, 2]),
                        )
                    ),
                    "name": "bend",
                },
                {
                    "func": partial(random_mockup, mockup_dir="coupon",
                                    offset=15),
                    "name": "mockup",
                },
            ]
        if name in ("newspaper",):
            self._post_processors = [
                # {'func':random_fold,'name':'fold'},
                # {'func':keepdata(scan),'name':'scan'},
                # {"func": show_label, "name": "label"}
            ]
        if name in ("form", "noline", "waybill", "express"):
            self._post_processors = [
                {"func": random_perspective, "name": None},
                {"func": random_rotate, "name": None},
                {
                    "func": partial(
                        random_background,
                        bg_dir=random.choice(
                            [
                                os.path.join(PROJECT_DIR,
                                             "static/background/wood"),
                                os.path.join(PROJECT_DIR,
                                             "static/background/stone"),
                            ]
                        ),
                        min_offset=20,
                        max_offset=50,
                    ),
                    "name": "bg",
                },
                {"func": random_gauss_noise, "name": "gs"},
            ]
        if name == "receipt":
            self._post_processors = [
                {
                    "func": keepdata(
                        partial(
                            distortion2,
                            peak=random.randint(1, 4),
                            period=random.choice([0.5, 0.75, 1, 1.5, 2]),
                            direction="y",
                        )
                    ),
                    "name": None,
                },
                {
                    "func": partial(
                        random_mockup,
                        mockup_dir="hand",
                        offset=5,
                        harmonize=harmonize,
                        crop=True,
                    ),
                    "name": "mockup",
                },
            ]
        
"""
