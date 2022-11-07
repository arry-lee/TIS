"""
图片工厂
职责：生成各类图片
命令：python factory.py -l si -m bankcard -o outdir -n 1000
"""
import os
import sys
import glob
import random
import shutil
import time
from functools import partial
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
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
sys.path.append(PROJECT_DIR)
# pylint: disable=wrong-import-position ungrouped-imports
from multilang.bankcard import BadTemplateError, BankCardDesigner
from general_table.bank_data_generator import (
    bank_detail_generator,
    bank_table_generator,
)
from multifaker import Faker
from multilang.formtemplate import FormTemplate, nolinetable2template
from multilang.htmltemplate import IDCardTemplate
from multilang.pdfire import from_pdf
from multilang.template import Template
from multilang.unilayout import UniForm
from post_processor.deco import c2p, keepdata
from post_processor.displace import displace, random_displace
from post_processor.distortion import distortion2
from post_processor.harmonizer import harmonize
from post_processor.label import log_label
from post_processor.mockup import random_mockup
from post_processor.qcode import barcode_image, qrcode_image
from post_processor.random import (
    random_background,
    random_gauss_noise,
    random_perspective,
    random_rotate,
    random_source,
)
from post_processor.shadow import add_shader
from utils.maxrect import max_left

__all__ = ["ImageMachine", "prepare_templates", "filter_templates", "filter_pdfs"]

DISPLACE_PAPER = os.path.join(PROJECT_DIR, "post_processor/displace/paper")


def iglob(path, ext):
    """
    生成目录 path 下后缀为ext的文件绝对路径
    :param path:
    :param ext:
    :return:
    """
    for i in glob.iglob(os.path.join(path, "*" + ext)):
        yield os.path.abspath(i)


def filter_templates(tpl_dir, filter_dir):
    """
    人工删除不好的效果图后，删去对应的模板
    :param tpl_dir: 模板目录
    :param filter_dir: 人工筛选剩余图片
    :return: 剩下的数量
    """
    filters = set()
    for fname in iglob(filter_dir, "g"):
        filters.add(os.path.splitext(os.path.basename(fname))[0])

    for tpl in iglob(tpl_dir, "tpl"):
        name = os.path.basename(tpl).removesuffix(".tpl")
        if name not in filters:
            os.remove(tpl)
            print(f"remove {tpl}")
    return len(filters)


def filter_pdfs(pdf_dir, filter_dir):
    """
    人工删除不好的效果图后，删去对应的PDF模板
    :param pdf_dir: pdf 目录
    :param filter_dir: 人工筛选剩余图片
    :return: 剩下的数量
    """
    filters = set()
    for fname in iglob(filter_dir, ".png"):
        filters.add(os.path.basename(fname).split("-")[0])

    for tpl in iglob(pdf_dir, "pdf"):
        name = os.path.basename(tpl).removesuffix(".pdf")
        if name not in filters:
            os.remove(tpl)
            print(f"remove {tpl}")
    return len(filters)


def prepare_templates(pdf_dir, tpl_dir, use_ocr=False):
    """
    准备模板文件夹
    :param pdf_dir: PDF 文件夹
    :param tpl_dir: 模板 文件夹
    :param use_ocr: 是否对PDF中的图片使用OCR识别,False 不识别
    :return: None
    """
    for file in tqdm(iglob(pdf_dir, ".pdf")):
        try:
            from_pdf(file, outdir=tpl_dir, maxpages=0, use_ocr=use_ocr)
        # pylint:disable=broad-except
        except (FileNotFoundError, Exception) as err:
            print(err)


def _save_and_log(image_data, fname, output_dir):
    """
    保存图片和标注到指定文件夹
    :param image_data: dict 图像字典
    :param fname: basename 命名 后缀又具体格式定
    :param output_dir: 输出路径
    :return: None
    """
    image = image_data["image"]
    name = f"{fname}.jpg"
    if isinstance(image, Image.Image):
        if image.mode == "RGBA":
            name = f"{fname}.png"
        image.save(os.path.join(output_dir, name))
    else:
        if image.shape[2] == 4:
            name = f"{fname}.png"
        cv2.imwrite(os.path.join(output_dir, name), image)
    log_label(
        os.path.join(output_dir, "%s.txt" % fname),
        name,
        image_data,
    )


class BaseGenerator:
    """各类图片生成器基类"""

    templates_basedir = os.path.join(BASE_DIR, "templates")

    def __init__(self, name):
        self.name = name

    def run(self, product_engine, **kwargs):
        """
        运行方法，无需重写
        :param product_engine: 假数据引擎
        :param lang: 语言
        :return: image_dict
        """
        template = self.load_template(**kwargs)
        self.preprocess(template)
        image_data = self.render_template(template, product_engine)
        image_data = self.postprocess(image_data, **kwargs)
        return image_data

    def preprocess(self, template):
        """模板预处理钩子，不同类型的预处理可能有所不同，原地处理"""

    # pylint: disable=unused-argument no-self-use
    def postprocess(self, image_data, **kwargs):
        """
        后处理钩子，不同的类型后处理可能有不同的后处理模式
        :param image_data: dict
        :return: dict
        """
        return image_data

    def render_template(self, template, engine):
        """
        模板渲染钩子
        :param template: 模板
        :param engine: 模板渲染引擎
        :return: imagedict
        """
        return NotImplemented

    def load_template(self, **kwargs):
        """模板加载钩子"""
        return NotImplemented


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
        template.set_bank_logo()
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
        _save_and_log(image_data, fname, product_dir)


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

    def render_template(self, template, engine):
        """
        渲染模板
        :param template: 模板
        :param engine: 模板渲染引擎
        :return:
        """
        template.replace_text(engine=engine)
        image_data = template.render_image_data_poison()  # 采用泊松编辑
        return image_data

    def postprocess(self, image_data, **kwargs):
        fname = kwargs.get("fname")
        product_dir = kwargs.get("product_dir")
        _save_and_log(image_data, fname + "_poisson", product_dir)

        image_data = self.postprocess_simple(image_data)
        _save_and_log(image_data, fname + "_simple", product_dir)

        image_data = self.postprocess_harmonizer(image_data)
        _save_and_log(image_data, fname + "_harmonized", product_dir)
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
        newmask = mask.point(lambda x: x - random.randint(0, 50) if x > 200 else x)
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

    @staticmethod
    def postprocess_harmonizer(image_data):
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
        draw.rounded_rectangle((0, 0) + size, 40, fill=255)
        res.putalpha(mask)

        image_data["image"] = res
        return image_data


class PassportGenerator(IDCardGenerator):
    """护照生成器"""

    def preprocess(self, template):
        pass


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
                img = engine.image(width, height)
                template.image.paste(img, text.rect.topleft)
                image_layer.paste(img, text.rect.topleft)

        for text in template.texts:
            width, height = text.rect.size
            if text.text in ("IMAGE", "image@", "<LTImage>"):
                continue

            font = ImageFont.truetype(font_path, height)
            text.text = engine.sentence_fontlike(font, width)
            text.font = font_path
            text.color = tuple(map(lambda x: x // 255 if x > 255 else x, text.color))
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
        # source_dir = r"E:\00IT\P\uniform\post_processor\displace\paper"
        # for i in tqdm(os.listdir(source_dir)):
        #     texture = os.path.join(source_dir, i)
        #     img = displace(image_layer, texture,ratio = 2)
        #     cv2.imwrite(texture+'.jpg',img)
        comp = random_displace(image_layer, ratio=2)
        # 和谐报纸上的图片显得不那么突兀
        comp = comp.convert("RGB")
        img = harmonize(comp, mask)
        image_data["image"] = cv2.cvtColor(np.asarray(img, np.uint8), cv2.COLOR_RGB2BGR)
        return image_data


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
                path = random_source(os.path.join(self.templates_dir, "images/"))
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
        # paper = random_source(r"E:\00IT\P\uniform\post_processor\displace\paper")
        # nbg = add_shader(bg, paper)
        # mask = displace(text_layer, paper, 2, mask_only=True)
        # nbg = c2p(nbg)
        # nbg.paste(mask, mask=mask)
        # image_data["image"] = nbg  # .convert('RGBA')
        del image_data["mask"]
        return image_data


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


class BusinessCardGenerator(TemplateGenerator):
    """名片生成器，采用模板方法"""


class VIPCardGenerator(BusinessCardGenerator):
    """VIP会员卡，复用名片模板，在文字层空白处加上 VIP 元素"""

    def __init__(self, name="vipcard"):
        super().__init__("businesscard")
        self.templates_dir = os.path.join(self.templates_basedir, name)

    def preprocess(self, template: Template):
        vip_sign = Image.open(random_source(os.path.join(self.templates_dir, "vip")))
        template.adjust_texts()

        rects = [text.rect for text in template.texts if text.text != "<LTImage>"]
        rect = max_left(rects)
        hmax = max(r.height for r in rects)
        height = min(2 * hmax, rect.height)
        vip_sign = vip_sign.resize((vip_sign.width * height // vip_sign.height, height))

        template.image.paste(vip_sign, rect.topleft, mask=vip_sign)
        template.add_round_corner(40)


class FormGenerator(TemplateGenerator):
    """表格生成器"""

    colors = [c for c in ImageColor.colormap if c != "black"]

    def __init__(self, name):
        super().__init__(name)
        self.config_file = os.path.join(self.templates_dir, "config.yaml")
        self.table_generator = UniForm(self.config_file)

    def load_template(self, **kwargs):
        table = next(self.table_generator.create())
        # 背景景随机有名色，前景颜色加深
        bg_color = ImageColor.getrgb(random.choice(self.colors))
        fg_color = bg_color[0] // 10, bg_color[1] // 10, bg_color[2] // 10
        template = FormTemplate.from_table(
            table, xy=(80, 80), bgcolor=bg_color, fgcolor=fg_color
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


class NoLineFormGenerator(FormGenerator):
    """无线表格生成"""

    def load_template(self, **kwargs):
        data = bank_detail_generator.create()[0]
        align = random.choice("lcr")
        table, multi = bank_table_generator(data, align=align)
        white_val = random.randint(230, 255)
        tmp = nolinetable2template(
            table,
            bgcolor=(white_val, white_val, white_val),
            line_pad=-2,
            watermark=False,
            dot_line=random.choice((True, False)),
            multiline=multi,
            vrules=random.choice(("all", None)),
        )
        return tmp


class WaybillGenerator(FormGenerator):
    """货运单生成器
    复用通用表格生成器
    配置文件在 ./templates/waybill/config.yaml
    """

    def preprocess(self, template):
        """加标题"""


class ExpressGenerator(FormGenerator):
    """快递单生成器
    复用通用表格生成器
    配置文件在 ./templates/express/config.yaml
    """

    def load_template(self, **kwargs):
        table = next(self.table_generator.create())
        # 背景景随机有名色，前景颜色加深
        white = random.randint(230, 255)
        black = random.randint(0, 30)
        bg_color = (white, white, white)
        fg_color = (black, black, black)
        template = FormTemplate.from_table(
            table, xy=(80, 80), bgcolor=bg_color, fgcolor=fg_color
        )
        color = random.choice([fg_color, "red", "blue"])
        for text in template.texts:
            text.color = random.choice([fg_color, color])
            text.font = random.choice(["b", "n", "i"])

        return template

    def preprocess(self, template):
        """加条形码"""
        qrcode_img = qrcode_image(template)
        height = 80
        qrcode_img = qrcode_img.resize((height, height))

        pty = random.choice([10, template.image.height - 90])

        template.image.paste(
            qrcode_img,
            (template.image.width - 160, pty),
            mask=qrcode_img.convert("L").point(lambda x: 255 - x),
        )

        num = "".join([str(random.randint(0, 9)) for i in range(12)])
        bar_img = barcode_image(num)
        bar_img = bar_img.resize((height * 520 // 200, height)).convert("RGB")
        template.image.paste(
            bar_img,
            (80, random.choice([10, template.image.height - 80])),
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


class ImageGenerator:
    """策略模式，根据名字来分配对应的生成器"""

    # pylint: disable=too-many-return-statements too-few-public-methods
    def __new__(cls, name=None):
        if name == "bankcard":
            return BankCardGenerator(name)
        if name in ("idcard",):
            return IDCardGenerator(name)
        if name == "passport":
            return PassportGenerator(name)
        if name in ("form", "waybill"):
            return FormGenerator(name)
        if name == "express":
            return ExpressGenerator(name)
        if name == "noline":
            return NoLineFormGenerator(name)
        if name == "receipt":
            return ReceiptGenerator(name)
        if name in ("newspaper", "magazine", "book"):
            return PaperGenerator(name)
        if name in ("coupons",):
            return CouponGenerator(name)
        if name == "menu":
            return MenuGenerator(name)
        if name == "businesscard":
            return BusinessCardGenerator(name)
        if name == "vipcard":
            return VIPCardGenerator(name)
        return TemplateGenerator(name)


class ImageMachine:
    """与具体的生成器类型无关的部分"""

    products_basedir = os.path.join(BASE_DIR, "output_data")

    def __init__(self, name):

        self._post_processors = []

        if name in ("bankcard", "idcard", "vipcard", "businesscard"):  # 样机指定
            self._post_processors = [
                {
                    "func": partial(random_mockup, mockup_dir="card"),
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
                    "func": partial(random_mockup, mockup_dir="coupon", offset=15),
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
                                r"E:\00IT\P\uniform\static\background\wood",
                                r"E:\00IT\P\uniform\static\background\stone",
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

        self.save_mid = True
        self.name = name
        self.generator = ImageGenerator(name)
        self.products_dir = os.path.join(self.products_basedir, name)

        self.engine = Faker  # 引擎类型

    def clean_output(self):
        """清理输出目录"""
        shutil.rmtree(self.products_dir)

    def fname(self, index, lang):
        """
        产品命名格式 可以重写
        :param index: 编号
        :param lang: 语种
        :return:
        """
        return f"{self.name}_{lang}_{index:08}_{int(time.time())}"

    def run(self, batch, lang):
        """
        运行
        :param batch: 批量
        :param lang: 语言
        :return:
        """
        product_dir = os.path.join(self.products_dir, lang)
        if not os.path.exists(product_dir):
            os.makedirs(product_dir, exist_ok=True)

        product_engine = self.engine(lang)  # 各个语言有一个引擎实例

        for index in tqdm(range(batch), unit=lang):
            fname = self.fname(index, lang)
            # pylint: disable=no-member
            image_data = self.generator.run(
                product_engine, lang=lang, fname=fname, product_dir=product_dir
            )
            # 后处理
            if self._post_processors:
                self.postprocess(image_data, fname, product_dir)
            else:
                _save_and_log(image_data, fname, product_dir)
        return True

    def postprocess(self, image_data, fname, product_dir):
        """
        后处理器钩子
        :param image_data: 图片字典
        :param fname: 命名
        :param product_dir: 保存文件夹
        :return:
        """
        for proc_dict in self._post_processors:
            processor = proc_dict.get("func")
            image_data = processor(image_data)
            if self.save_mid and proc_dict.get("name", None):
                fname = fname + "_" + proc_dict.get("name")
                _save_and_log(image_data, fname, product_dir)


def main(mode, batch=10, lang=None):
    """
    主程序入口
    :param mode: 种类名
    :param batch: 数量
    :param lang: 语种
    :return: None
    """
    if not lang:
        langs = [
            "cs",
            "fil_PH",
            "el_GR",
            "id",
            "lo_LA",
            "ms_MY",
            "ne",
            "nl_be",
            "si",
            "bn",
            "km",
        ]
    else:
        langs = [lang]
    machine = ImageMachine(mode)
    machine.clean_output()
    for one in langs:
        machine.run(batch, one)


if __name__ == "__main__":
    import argparse
    from settings import TEMPLATES_MAP, LANG_TUPLE

    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", help=f"mode, one of {TEMPLATES_MAP}")
    parser.add_argument("-b", "--batch", type=int, help="batch size")
    parser.add_argument(
        "-l",
        "--lang",
        default=None,
        help=f"lang code, one of {[(i[0],i[2]) for i in LANG_TUPLE]}",
    )
    args = parser.parse_args()

    main(args.mode, args.batch, args.lang)

    # 准备模板 加人工过滤
    # prepare_templates('./templates/businesscard', './templates/businesscard')
    # x = filter_templates('./templates/businesscard/', './templates/businesscard/filter/')
    # print(x)
    # prepare_templates('./templates/coupons/en','./templates/coupons')
    # prepare_templates('./templates/book/','./templates/book/')
    # prepare_templates(r'E:\00IT\P\pdfspider\data\newspaper','./templates/newspaper')
    # prepare_templates('./templates/menu/el_GR','./output_data/menu/el_GR')
    # prepare_templates('./templates/coupons/bn','./output_data/coupons/bn')
    #
    # num = filter_templates('./templates/coupons/','./output_data/coupons/filters/')
    # print(num)
    # prepare_templates('./templates/waybill/pdfs', './templates/waybill')
    # main("passport", 2)
    # for mode in ("form","receipt","express","noline","businesscard","vipcard"):
    #     main(mode, 5)
    # main("bankcard", 10)
    # for js in iglob(r"E:\00IT\P\uniform\multilang\mockup\res\hand",'json')
