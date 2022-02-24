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

from awesometable import banktable2image, table2image
from data_generator import bank_detail_generator, bank_table_generator
from data_generator.fakekeys import read_background
from data_generator.uniform import UniForm
from fs_data import FinancialStatementTable, fstable2image, fstable2image_en
from post_processor import random as _random
from post_processor.background import add_background_data
from post_processor.deco import keepdata
from post_processor.label import log_label, show_label
from post_processor.seal import gen_seal, add_seal

from post_processor.random import random_seal, random_fold, random_distortion, \
    random_noise, random_rotate, random_perspective, random_background, \
    random_pollution

from static.logo import get_logo_path
from utils.ulpb import encode


class Factory(Thread):
    """工厂模式"""

    def __init__(self, batch):
        super().__init__()
        self.batch = batch
        self.data_generator = bank_detail_generator  # >data
        self.table_generator = bank_table_generator  # data > table
        self.image_compositor = banktable2image  # table > image
        self.post_processor = [
            {'func': random_seal, 'ratio': 0.4},
            {'func': random_pollution, 'ratio': 0},
            {'func': random_fold, 'ratio': 0.5},
            {'func': random_noise, 'ratio': 0.5},
            {'func': random_distortion, 'ratio': 1},
            {'func': random_rotate, 'ratio': 0.3},
            {'func': random_perspective, 'ratio': 0.3},
            {'func': random_background, 'ratio': 0.3},
            {'func': show_label, 'ratio': 1},
        ]

        with open('config/post_processor_config.yaml', 'r',encoding='utf-8') as f:
            self.post_processor_config = yaml.load(f, Loader=yaml.SafeLoader)
        self.post_processor = []
        for k,v in self.post_processor_config.items():
            ratio = v.pop('ratio')
            func = partial(getattr(_random, k),**v)
            self.post_processor.append({'func':func,'ratio':ratio})

        self.output_dir = './data/bank/'
        self.save_mid = False

    def _save_and_log(self, image_data, fn):
        cv2.imwrite(os.path.join(self.output_dir, '%s.jpg' % fn),
                    image_data['image'])
        log_label(os.path.join(self.output_dir, '%s.txt' % fn), '%s.jpg' % fn,
                  image_data)

    def run(self):
        pbar = tqdm(total=self.batch)
        pbar.set_description("Factory")
        print('start')
        sealdir = self.post_processor_config['random_seal']['seal_dir']
        bg_dir = self.post_processor_config['random_background']['bg_dir']
        for data in self.data_generator.create(iterations=self.batch):
            bankname = data['银行']
            align = random.choice('lcr')
            table,multi = self.table_generator(data, align=align)
            c = random.randint(230, 255)
            image_data = self.image_compositor(table,
                                               bgcolor=(c, c, c),
                                               line_pad=-2,
                                               logo_path=get_logo_path(
                                                   bankname),
                                               watermark=False,
                                               dot_line=random.choice((True,False)),
                                               multiline = multi)

            if self.save_mid:
                fn = '0' + str(int(time.time() * 1000))[5:]
                self._save_and_log(image_data, fn)

            sealname = os.path.join(sealdir, encode(bankname) + '.jpg')
            if not os.path.exists(sealname):
                print(sealname)
                seal = gen_seal(bankname + '南京市分行')
                cv2.imwrite(sealname, seal)

            # 银行印章不随机
            self.post_processor[0]['func'] = keepdata(partial(add_seal, seal_p=sealname))

            for fno, fd in enumerate(self.post_processor, start=1):
                if random.random() < fd['ratio']:
                    func = fd.get('func')
                    print(func)
                    image_data = func(image_data)  # 默认参数就是随机的
                    if self.save_mid:
                        fn = str(fno) + fn[1:]
                        self._save_and_log(image_data, fn)
            else:
                if not func is self.post_processor[-1]['func']:
                    white = np.ones_like(image_data['image'])*255
                    image_data = add_background_data(image_data,white,0)

            if not self.save_mid:
                fn = '0' + str(int(time.time() * 1000))[5:]
                self._save_and_log(image_data, fn)

                pbar.update(1)
        pbar.close()


class UniFactory(Thread):
    def __init__(self, config, batch):
        super().__init__()
        self.batch = batch

        if isinstance(config, dict):
            self.config = config
        elif isinstance(config, str):
            with open(config, 'r',encoding='utf-8') as f:
                self.config = yaml.load(f, Loader=yaml.SafeLoader)

        self.table_generator = UniForm(self.config)
        bg_dir = self.config['base']['bg_dir']

        self.background_generator = cycle(read_background(bg_dir))

        post_processor_config = self.config['post_processor']
        self.post_processor = []
        for k,v in post_processor_config.items():
            ratio = v.pop('ratio')
            func = partial(getattr(_random, k),**v)
            self.post_processor.append({'func':func,'ratio':ratio})

        self._type = self.config['base']['type']

    def run(self):
        pbar = tqdm(total=self.batch)
        pbar.set_description("Threading %s" % self._type)
        output_dir = self.config['base']['output_dir']
        bg_dir = self.config['post_processor']['random_background']['bg_dir']
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        self.save_mid = self.config['base'].get('save_mid', False)

        for t in self.table_generator.create(self.batch):

            if self.background_generator is None:
                bg = None
                bg_box = None
            else:
                bg, bg_box = self.background_generator.__next__()

            fn = '0' + str(int(time.time() * 1000))[5:]
            image_data = table2image(t,
                                     (0, 0),
                                     font_size=20,
                                     line_pad=0,
                                     bg_box=bg_box,
                                     background=bg)

            if self.save_mid:
                cv2.imwrite(os.path.join(output_dir, '%s.jpg' % fn),
                            image_data['image'])
                log_label(os.path.join(output_dir, '%s.txt' % fn), '%s.jpg' % fn,
                          image_data)

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
                else: # 如果最后没有使用到 背景，就无偏的增加白底
                    if not func is self.post_processor[-1]['func']:
                        white = np.ones_like(image_data['image'])*255
                        image_data = add_background_data(image_data, white, 0)

            if not self.save_mid:
                cv2.imwrite(os.path.join(output_dir, '%s.jpg' % fn),
                            image_data['image'])
                log_label(os.path.join(output_dir, '%s.txt' % fn), '%s.jpg' % fn,
                          image_data)
            pbar.update(1)
        pbar.close()


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
        # self.table_generator = FinancialStatementTable(name,config)  # data > table
        if lang == 'zh_CN':
            self.image_compositor = fstable2image  # table > image
            self.output_dir = './data/financial_statement/'
        else:
            self.image_compositor = fstable2image_en
            self.output_dir = './data/financial_statement_en/'
        self.background_generator = None
        self.post_processor = [
        #     {'func': random_seal, 'ratio': 0.4},
        #     {'func': random_pollution, 'ratio': 0},
        #     {'func': random_fold, 'ratio': 0.5},
        #     {'func': random_noise, 'ratio': 0.5},
        #     {'func': random_distortion, 'ratio': 1},
        #     {'func': random_rotate, 'ratio': 0.3},
        #     {'func': random_perspective, 'ratio': 0.3},
        #     {'func': random_background, 'ratio': 0.3},
            {'func': show_label, 'ratio': 1},
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
        pbar = tqdm(total=self.batch)
        pbar.set_description("FsFactory")
        # print('start')
        # sealdir = self.post_processor_config['random_seal']['seal_dir']
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

def main(argv):
    type = argv[1]
    batch = int(argv[2])
    if type == 'bank':
        f = Factory(batch)
    else:
        config = 'config/%s.yaml'% type
        f = UniFactory(config=config,batch=batch)
    f.start()

if __name__ == '__main__':
    # import sys
    # main(sys.argv)
    # bank_factory = Factory(batch=10)
    # bank_factory.start()
    fsfactory = FSFactory('all',25,lang='zh_CN',need_proc=False)
    fsfactory.start()