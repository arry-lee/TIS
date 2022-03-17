import os
import random
import re
import time
from functools import partial
from itertools import cycle
from threading import Thread

import cv2
import numpy as np
import yaml
from tqdm import tqdm

from fs_data import FinancialStatementTable, fstable2image, fstable2image_en
from fs_designer import LayoutDesigner
from post_processor import random as _random
from post_processor.background import add_background_data
from post_processor.label import log_label
from post_processor.random import random_perspective


class FSFactory(Thread):
    """工厂模式"""
    BOLD_PATTERN = re.compile(r'.*[其项合总年]*[中目计前额].*')
    BACK_PATTERN = re.compile(r'[一二三四五六七八九十]+.*')
    def __init__(self, type, batch,lang='zh_CN',need_proc=True):
        super().__init__()
        self.batch = batch
        if lang == 'zh_CN':
            config = './config/fs_config_zh.yaml'
        else:
            config = './config/fs_config_en.yaml'

        with open(config, 'r', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
        if type == 'all':
            names = list(config.keys())
        else:
            names = [n for n in config.keys() if type in n]

        self.table_machines = [FinancialStatementTable(name,lang) for name in names]
        self.fst = None
        if lang == 'zh_CN':
            self.image_compositor = fstable2image  # table > image
            self.output_dir = './data/financial_statement/'
        elif lang == 'en' and type != 'sp':
            self.image_compositor = fstable2image_en
            self.output_dir = './data/financial_statement_en/'
        elif lang == 'en' and type == 'sp':
            self.fst = LayoutDesigner()
            self.output_dir = './data/financial_statement_en/'

        self.background_generator = None
        self.post_processor = [
        #     {'func': random_seal, 'ratio': 0.4},
        #     {'func': random_pollution, 'ratio': 0},
        #     {'func': random_fold, 'ratio': 0.5},
        #     {'func': random_noise, 'ratio': 0.5},
        #     {'func': random_distortion, 'ratio': 1},
        #     {'func': random_rotate, 'ratio': 0.3},
        #     {'func': random_perspective, 'ratio': 1},
        #     {'func': random_background, 'ratio': 0.3},
        #     {'func': show_label, 'ratio': 1},
        ]

        if need_proc:
            with open('config/post_processor_config.yaml', 'r',encoding='utf-8') as f:
                self.post_processor_config = yaml.load(f, Loader=yaml.SafeLoader)
            self.post_processor = []
            for k,v in self.post_processor_config.items():
                ratio = v.pop('ratio')
                func = partial(getattr(_random, k),**v)
                self.post_processor.append({'func':func,'ratio':ratio})

        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
        self.save_mid = False

    def _save_and_log(self, image_data, fn):
        cv2.imwrite(os.path.join(self.output_dir, '%s.jpg' % fn),
                    image_data['image'])
        log_label(os.path.join(self.output_dir, '%s.txt' % fn), '%s.jpg' % fn,
                  image_data)

    def run(self):
        output_dir = self.output_dir

        if self.fst:
            self.fst.run(self.batch,output_dir)
            return

        pbar = tqdm(total=self.batch)
        pbar.set_description("FsFactory")
        count = 0
        for table_generator in cycle(self.table_machines):
            for t in table_generator.create(5,page_it=False):
                fn = '0' + str(int(time.time() * 1000))[5:]
                if random.random()<0.5:
                    back_pattern = self.BACK_PATTERN
                else:
                    back_pattern = None

                image_data = self.image_compositor(t,line_pad=-2,offset=10,bold_pattern=self.BOLD_PATTERN,back_pattern=back_pattern)

                if self.save_mid:
                    cv2.imwrite(os.path.join(output_dir, '%s.jpg' % fn),
                                image_data['image'])
                    log_label(os.path.join(output_dir, '%s.txt' % fn),
                              '%s.jpg' % fn,
                              image_data)
                    if count>=self.batch:
                        return
                    else:
                        count+=1

                if self.post_processor:
                    for fno, fd in enumerate(self.post_processor, start=1):
                        if random.random() < fd['ratio']:
                            func = fd.get('func')
                            image_data = func(image_data)  # 默认参数就是随机的
                            if self.save_mid:
                                fn = str(fno) + fn[1:]
                                cv2.imwrite(os.path.join(output_dir, '%s.jpg' % fn),
                                            image_data['image'])
                                log_label(os.path.join(output_dir, '%s.txt' % fn),
                                          '%s.jpg' % fn, image_data)
                                if count >= self.batch:
                                    return
                                else:
                                    count += 1
                    else:  # 如果最后没有使用到 背景，就无偏的增加白底
                        if not func is self.post_processor[-1]['func']:
                            white = np.ones_like(image_data['image']) * 255
                            image_data = add_background_data(image_data, white, 0)

                if not self.save_mid:
                    cv2.imwrite(os.path.join(output_dir, '%s.jpg' % fn),
                                image_data['image'])
                    log_label(os.path.join(output_dir, '%s.txt' % fn),
                              '%s.jpg' % fn,
                              image_data)
                    if count>=self.batch:
                        return
                    else:
                        count += 1
                pbar.update(1)
        pbar.close()



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="中英文财务报表图片合成工具")
    parser.add_argument("type", type=str, choices=['all', 'sp'],
                        help="sp only for en")
    parser.add_argument("lang", type=str, choices=['zh_CN', 'en'],help="zh_CN or en")
    parser.add_argument("batch", type=int, help="总量")
    parser.add_argument("-p", "--post_process", action="store_true")
    args = parser.parse_args()
    ff = FSFactory(args.type,args.batch,args.lang,need_proc=args.post_process)
    ff.run()
