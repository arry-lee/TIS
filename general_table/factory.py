"""
通用表格工厂函数
"""
import os
import random
import time
from functools import partial
from itertools import cycle
from threading import Thread

import cv2
import numpy as np
import yaml
from tqdm import tqdm

from awesometable.table2image import table2image
from post_processor import random as _random
from post_processor.background import add_background_data
from post_processor.deco import keepdata
from post_processor.label import log_label, show_label
from post_processor.random import (
    random_background,
    random_distortion,
    random_fold,
    random_noise,
    random_perspective,
    random_pollution,
    random_rotate,
    random_seal,
)
from post_processor.seal import add_seal, gen_seal
from static.logo import get_logo_path
from utils.ulpb import encode
from .bank_data_generator import bank_detail_generator, bank_table_generator
from .bank_data_generator import banktable2image
from .fakekeys import read_background
from .uniform import UniForm


class BackTableFactory(Thread):
    """工厂模式"""

    def __init__(self, batch):
        super().__init__()
        self.batch = batch
        self.data_generator = bank_detail_generator  # >data
        self.table_generator = bank_table_generator  # data > table
        self.image_compositor = banktable2image  # table > image
        self.post_processor = [
            {"func": random_seal, "ratio": 0.4},
            {"func": random_pollution, "ratio": 0},
            {"func": random_fold, "ratio": 0.5},
            {"func": random_noise, "ratio": 0.5},
            {"func": random_distortion, "ratio": 1},
            {"func": random_rotate, "ratio": 0.3},
            {"func": random_perspective, "ratio": 0.3},
            {"func": random_background, "ratio": 0.3},
            {"func": show_label, "ratio": 1},
        ]

        with open("config/post_processor_config.yaml", "r", encoding="utf-8") as cfg:
            self.post_processor_config = yaml.load(cfg, Loader=yaml.SafeLoader)
        self.post_processor = []
        for key, val in self.post_processor_config.items():
            ratio = val.pop("ratio")
            func = partial(getattr(_random, key), **val)
            self.post_processor.append({"func": func, "ratio": ratio})

        self.output_dir = "../data/bank/"
        self.save_mid = False

    def _save_and_log(self, image_data, fname):
        cv2.imwrite(
            os.path.join(self.output_dir, "%s.jpg" % fname), image_data["image"]
        )
        log_label(
            os.path.join(self.output_dir, "%s.txt" % fname),
            "%s.jpg" % fname,
            image_data,
        )

    def run(self):
        pbar = tqdm(total=self.batch)
        pbar.set_description("Factory")
        print("start")
        sealdir = self.post_processor_config["random_seal"]["seal_dir"]
        for data in self.data_generator.create(iterations=self.batch):
            bankname = data["银行"]
            align = random.choice("lcr")
            table, multi = self.table_generator(data, align=align)
            white_val = random.randint(230, 255)
            image_data = self.image_compositor(
                table,
                bgcolor=(white_val, white_val, white_val),
                line_pad=-2,
                logo_path=get_logo_path(bankname),
                watermark=False,
                dot_line=random.choice((True, False)),
                multiline=multi,
            )

            if self.save_mid:
                fname = "0" + str(int(time.time() * 1000))[5:]
                self._save_and_log(image_data, fname)

            seal_name = os.path.join(sealdir, encode(bankname) + ".jpg")
            if not os.path.exists(seal_name):
                seal = gen_seal(bankname + "南京市分行")
                cv2.imwrite(seal_name, seal)

            # 银行印章不随机
            self.post_processor[0]["func"] = keepdata(
                partial(add_seal, seal_p=seal_name)
            )
            func = None
            for fno, proc in enumerate(self.post_processor, start=1):
                if random.random() < proc["ratio"]:
                    func = proc.get("func")
                    image_data = func(image_data)  # 默认参数就是随机的
                    if self.save_mid:
                        fname = str(fno) + fname[1:]
                        self._save_and_log(image_data, fname)

            if not func is self.post_processor[-1]["func"]:
                white = np.ones_like(image_data["image"]) * 255
                image_data = add_background_data(image_data, white, 0)

            if not self.save_mid:
                fname = "0" + str(int(time.time() * 1000))[5:]
                self._save_and_log(image_data, fname)
                pbar.update(1)
        pbar.close()


class GeneralTableFactory(Thread):
    """通用表格工厂"""

    def __init__(self, config, batch):
        super().__init__()
        self.save_mid = self.config["base"].get("save_mid", False)
        self.batch = batch

        if isinstance(config, dict):
            self.config = config
        elif isinstance(config, str):
            with open(config, "r", encoding="utf-8") as cfg:
                self.config = yaml.load(cfg, Loader=yaml.SafeLoader)

        self.table_generator = UniForm(self.config)
        bg_dir = self.config["base"]["bg_dir"]

        self.background_generator = cycle(read_background(bg_dir))

        post_processor_config = self.config["post_processor"]
        self.post_processor = []
        for key, val in post_processor_config.items():
            ratio = val.pop("ratio")
            func = partial(getattr(_random, key), **val)
            self.post_processor.append({"func": func, "ratio": ratio})

        self._type = self.config["base"]["type"]

    def run(self):
        pbar = tqdm(total=self.batch)
        pbar.set_description("Threading %s" % self._type)
        output_dir = self.config["base"]["output_dir"]
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        for tab in self.table_generator.create(self.batch):

            if self.background_generator is None:
                background = None
                bg_box = None
            else:
                background, bg_box = self.background_generator.__next__()

            fname = "0" + str(int(time.time() * 1000))[5:]
            image_data = table2image(
                tab,
                xy=(0, 0),
                font_size=20,
                line_pad=0,
                bg_box=bg_box,
                background=background,
            )

            if self.save_mid:
                cv2.imwrite(
                    os.path.join(output_dir, "%s.jpg" % fname), image_data["image"]
                )
                log_label(
                    os.path.join(output_dir, "%s.txt" % fname),
                    "%s.jpg" % fname,
                    image_data,
                )
            func = None
            if self.post_processor:
                for fno, proc in enumerate(self.post_processor, start=1):
                    if random.random() < proc["ratio"]:
                        func = proc.get("func")
                        image_data = func(image_data)  # 默认参数就是随机的
                        if self.save_mid:
                            fname = str(fno) + fname[1:]
                            cv2.imwrite(
                                os.path.join(output_dir, "%s.jpg" % fname),
                                image_data["image"],
                            )
                            log_label(
                                os.path.join(output_dir, "%s.txt" % fname),
                                "%s.jpg" % fname,
                                image_data,
                            )
                # 如果最后没有使用到 背景，就无偏的增加白底
                if not func is self.post_processor[-1]["func"]:
                    white = np.ones_like(image_data["image"]) * 255
                    image_data = add_background_data(image_data, white, 0)

            if not self.save_mid:
                cv2.imwrite(
                    os.path.join(output_dir, "%s.jpg" % fname), image_data["image"]
                )
                log_label(
                    os.path.join(output_dir, "%s.txt" % fname),
                    "%s.jpg" % fname,
                    image_data,
                )
            pbar.update(1)
        pbar.close()


def main(argv):
    """
    :param argv: mode 'bank' or other config
    :return: None
    """
    mode = argv[1]
    batch = int(argv[2])
    if mode == "bank":
        factory = BackTableFactory(batch)
    else:
        config = "config/%s.yaml" % mode
        factory = GeneralTableFactory(config=config, batch=batch)
    factory.start()


if __name__ == "__main__":
    import sys

    main(sys.argv)
