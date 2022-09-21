"""
图片工厂
职责：生成各类图片
命令：python factory.py -l si -m bankcard -o outdir -n 1000
"""

import glob
import os
import random
from itertools import cycle

import cv2
from tqdm import tqdm

from multifaker import Faker
from multilang.baidu import BaiduTranslator
from pdfire import from_pdf
from post_processor.label import log_label
from template import Template, TemplateError

from post_processor.scan import spread, scan
from post_processor.deco import keepdata

from card_template import BankCardDesigner


def iglob(dir, ext):
    for i in glob.iglob(os.path.join(dir, "*" + ext)):
        yield os.path.abspath(i)


def prepare_templates(pdf_dir, tpl_dir):
    """准备模板文件夹"""
    for file in tqdm(iglob(pdf_dir, ".pdf")):
        from_pdf(file, outdir=tpl_dir)


def _save_and_log(image_data, fname, output_dir):
    cv2.imwrite(os.path.join(output_dir, "%s.jpg" % fname), image_data["image"])
    log_label(
        os.path.join(output_dir, "%s.txt" % fname),
        "%s.jpg" % fname,
        image_data,
    )


class BankCardGenerator:
    """银行卡生成器
    生成器的属性只有一个名字
    只有一个run接口，该接口只有一个必须参数lang，每次调用生成一个图片
    """

    def __init__(self, name):
        self.name = name

    def run(self, faker):
        """
        只有一个run接口，该接口只有一个必须参数lang，每次调用生成一个图片
        :param faker: 引擎
        :param face: 正反面 'back' 反面 'front' 正面
        :return: dict
        """
        bankcard = BankCardDesigner.random_template()
        bankcard.add_round_corner()
        bankcard.set_bank_logo()
        number = " ".join([str(random.randint(1000, 9999)) for _ in range(4)])
        bankcard.set_card_number(number)
        name = faker.sentence(2)
        bankcard.set_cardholder_name(name, faker.font())
        legend = faker.sentence(4)
        bankcard.set_legend(legend, faker.font())
        bankcard.set_signature(name, faker.font())
        face = random.choice(["back", "front"])
        image_data = bankcard.get_data(face)
        return image_data

    def postprocess(self, image_data):
        """
        银行卡，先加mockup
        :return:
        """


class TemplateGenerator:
    """
    模板生成器
    单一职责是渲染一个模板并生成
    """

    templates_basedir = "templates"

    def __init__(self, name):
        self.name = name
        self.templates_dir = os.path.join(self.templates_basedir, name)
        self._templates = cycle(iglob(self.templates_dir, ".tpl"))

    def run(self, product_engine):
        """
        运行
        :param lang: 语言
        :return: image_dict
        """
        template_path = next(self._templates)
        template = Template.load(template_path)
        # 实际生产
        self.preprocess(template)
        template.replace_text(engine=product_engine)
        image_data = template.render_image_data()
        image_data = self.postproces(image_data)
        return image_data

    def preprocess(self, template):
        """模板预处理钩子，不同类型的预处理可能有所不同，原地处理"""

    def postproces(self, image_data):
        """
        后处理钩子，不同的类型后处理可能有不同的后处理模式
        :param image_data: dict
        :return: dict
        """
        return image_data


class ImageGenerator:
    """策略"""

    def __new__(cls, name=None):
        if name == "bankcard":
            return BankCardGenerator(name)
        return TemplateGenerator(name)


class ImageMachine:
    """与具体的生成器类型无关的部分"""

    products_basedir = "output_data"

    def __init__(self, name):
        self._post_processors = []
        self.save_mid = False
        self.name = name
        self.generator = ImageGenerator(name)
        print(self.generator)
        self.products_dir = os.path.join(self.products_basedir, name)

        self.engine = Faker  # 引擎类型

    def fname(self, index, lang):
        """
        产品命名格式 可以重写
        :param index: 编号
        :param lang: 语种
        :param template_path: 模板路径
        :param processor_name: 后处理
        :return:
        """
        return f"{self.name}_{lang}_{index:08}"

    def run(self, batch, lang):
        """
        运行
        :param batch: 批量
        :param lang: 语言
        :return:
        """
        product_dir = os.path.join(self.products_dir, lang)
        product_engine = self.engine(lang)  # 各个语言有一个引擎实例

        for index in tqdm(range(batch)):
            fname = self.fname(index, lang)
            # 实际生产
            image_data = self.generator.run(product_engine)
            _save_and_log(image_data, fname, product_dir)
            # 后处理
            self.postprocess(image_data, fname, product_dir)

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
            if self.save_mid:
                fname = fname + "_" + proc_dict.get("name")
                _save_and_log(image_data, fname, product_dir)


class BaseMachine:
    """
    生产机器的基类
    pdf 渲染类型的:
    book
    businesscard
    coupons
    magazine
    menu
    newspaper
    vipcard
    设计类型的
    bankcard
    生成类型的
    form
    receipt
    express
    标注转换类型的
    idcard
    passport
    不规则类型的
    passport

    """

    templates_basedir = "templates"
    products_basedir = "output_data"

    def __init__(self, mode):
        """
        定义一个机器基类，需要定义类型，语言只是产品的一个参数，不应该放在这里
        :param mode: 产品
        """
        super().__init__()
        self.mode = mode
        self.templates_dir = os.path.join(self.templates_basedir, mode)
        self.products_dir = os.path.join(self.products_basedir, mode)
        self._engine = Faker
        self._templates = cycle(iglob(self.templates_dir, ".tpl"))

        self._post_processors = (
            []
        )  # [{'func':keepdata(scan),'name':'scan'}]  # 各个子类可以自定
        self.save_mid = True

    @property
    def engine(self):
        return self._engine

    @engine.setter
    def engine(self, val):
        """设置翻译引擎，默认是Faker"""
        if val.lower() == "faker":
            self._engine = Faker
        elif val.lower == "trans":
            self._engine = BaiduTranslator
        else:
            raise KeyError("No such engine, use faker or trans")

    def preprocess(self, template):
        """
        预处理钩子，此处处理模板
        :param template: 模板
        :return: template
        """
        return template

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
            if self.save_mid:
                fname = fname + "_" + proc_dict.get("name")
                self._save_and_log(image_data, fname, product_dir)

    def produce(self, template, product_engine):
        """
        处理单个模板，使用 对应语言的引擎
        :param template_path:
        :param product_engine:
        :return:
        """
        template.replace_text(engine=product_engine)
        image_data = template.render_image_data()
        return image_data

    def _save_and_log(self, image_data, fname, output_dir):
        cv2.imwrite(os.path.join(output_dir, "%s.jpg" % fname), image_data["image"])
        log_label(
            os.path.join(output_dir, "%s.txt" % fname),
            "%s.jpg" % fname,
            image_data,
        )

    def fname(self, index, lang, template_path):
        """
        产品命名格式 可以重写
        :param index: 编号
        :param lang: 语种
        :param template_path: 模板路径
        :param processor_name: 后处理
        :return:
        """
        _, name = os.path.split(template_path)
        temp, _ = name.split(".")
        return f"{self.mode}_{lang}_{temp}_{index:08}"

    def run(self, batch, lang):
        """
        机器运行的时候需要指定批量和语言
        :param lang: 语言
        :param batch: 批量
        :return:
        """
        product_dir = os.path.join(self.products_dir, lang)
        product_engine = self.engine(lang)  # 具体语言的引擎

        for index in tqdm(range(batch)):
            template_path = next(self._templates)
            fname = self.fname(index, lang, template_path)
            template = Template.load(template_path)
            # 模板预处理
            self.preprocess(template)
            # 实际生产
            image_data = self.produce(template, product_engine)
            self._save_and_log(image_data, fname, product_dir)
            # 后处理
            self.postprocess(image_data, fname, product_dir)


if __name__ == "__main__":
    # prepare_templates('./templates/menu/bn','./templates/menu')
    a = ImageMachine("bankcard")
    a.run(3, "si")
