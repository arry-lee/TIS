import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output_data")
sys.path.append(PROJECT_DIR)

import shutil
import time

from tqdm import tqdm

from tasks.multilang.factory import *
from postprocessor.label import save_and_log
from register import IMAGE_GENERATOR_REGISTRY


class ImageMachine:
    """与具体的生成器类型无关的部分"""

    products_basedir = OUTPUT_DIR

    def __init__(self, name):
        self._post_processors = []
        self.save_mid = True
        self.name = name
        self.generator = IMAGE_GENERATOR_REGISTRY.get(name)(name)
        self.products_dir = os.path.join(self.products_basedir, name)
        self.engine = Faker  # 引擎类型

    def clean_output(self):
        """清理输出目录"""
        shutil.rmtree(self.products_dir)

    def fname(self, index, lang):
        """产品命名格式 可以重写

        :param index: 编号
        :param lang: 语种
        :return:
        """
        return f"{self.name}_{lang}_{index:08}_{int(time.time())}"

    def run(self, batch, lang):
        """运行

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
                save_and_log(image_data, fname, product_dir)
        return True

    def postprocess(self, image_data, fname, product_dir):
        """后处理器钩子

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
                save_and_log(image_data, fname, product_dir)


from tasks.arc_text.main import main as arctext
from tasks.general_table.factory import BackTableFactory
from tasks.financial_statement.fs_factory import FSFactory


def main(mode, batch=10, lang=None, clear_output=False):
    """
    The main function is the entry point for the program.
    It creates an ImageMachine object and calls its run method to generate images.


    :param mode: Specify the type of images to download
    :param batch=10: Specify the number of images to be generated
    :param lang=None: Specify the language of the images to be downloaded
    :param clear_output=False: Prevent the output folder from being cleared every time you run this script
    :return: None
    :doc-author: Trelent
    """
    """主程序入口
    
    :param mode: 种类名
    :param batch: 数量
    :param lang: 语种
    :return: None
    """
    if mode == "arctext":
        if lang and lang != "zh_CN":
            raise ValueError("The lang of arctext only support 'zh_CN'")
        return arctext(batch)

    if mode == "financial_statement" or mode == "fs":
        if lang not in ("zh_CN", "en"):
            raise ValueError(
                "The lang of financial_statement only support 'zh_CN' and 'en'"
            )
        ff = FSFactory("all", batch, lang, need_proc=True)
        ff.run()

    if mode == "layout":
        if lang not in ("zh_CN", "en"):
            raise ValueError(
                "The lang of financial_statement only support 'zh_CN' and 'en'"
            )
        ff = FSFactory("sp", batch, lang, need_proc=True)
        ff.run()

    if mode == "bankflow":
        factory = BackTableFactory(batch)
        factory.start()

    if mode.endswith(".yaml"):
        # config = "config/%s.yaml" % mode
        factory = GeneralTableFactory(config=mode, batch=batch, use_faker=True)
        factory.start()

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
    if clear_output:
        machine.clean_output()
    for one in langs:
        machine.run(batch, one)


if __name__ == "__main__":
    import argparse
    import logging

    logging.basicConfig(
        level=logging.INFO,
        filename="log.log",
        filemode="w",
        datefmt="%a, %d %b %Y %H:%M:%S",
        format="%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s",
    )

    from multifaker import Faker, LANG_TUPLE

    mode_list = list(IMAGE_GENERATOR_REGISTRY.keys()) + [
        "arctext",
        "financial_statement",
        "layout",
        "bankflow",
    ]
    mode_list.sort()

    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", help=f"mode, one of {'|'.join(mode_list)}")
    parser.add_argument("-b", "--batch", type=int, help="batch size")

    langs = ["中文:zh_CN", "英语:en"] + [f"{i[2]}:{i[0]}" for i in LANG_TUPLE]
    lang_str = ",".join(langs)

    parser.add_argument(
        "-l",
        "--lang",
        default=None,
        help=f"lang code, one of {lang_str}",
    )
    parser.add_argument("--clear_output", help="清空mode类输出文件夹下所有内容", action="store_true")
    args = parser.parse_args()

    main(args.mode, args.batch, args.lang, args.clear_output)
