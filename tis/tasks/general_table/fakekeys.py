"""
语料生成器

1.将所有的词条准备好
2.按长度分组,长度小于6的视为 key 且不是纯数字，出现次数大于2的
3.长度大于20 的为multitext
4.只出现1次的视为值
"""

import glob
import os
import re
from collections import Counter, defaultdict


def key_value_generator(basedir, key_thresh_hold=None):
    """
    :param basedir: 存放标注数据的文件夹
    :param key_thresh_hold: 视为键的数量阈值
    :return: keys_dict, values_dict, text, keys, values
    """
    texts = glob.glob(os.path.join(basedir, "*.txt"))
    counter = Counter()
    for text in texts:
        with open(text, "r", encoding="gbk", errors="ignore") as file:
            for line in file:
                word = line.strip().split("@")[-1]
                if len(word) > 1:
                    counter.update({word: 1})

    keys = []
    values = []
    text = []
    if key_thresh_hold is None:
        key_thresh_hold = counter.most_common(1)[0][1] // 2

    d_pat = re.compile(r".*\d.*")  # 任何纯数字的
    for word, cnt in counter.items():
        # 重复数量过多而且不是数字，视为键
        if cnt > key_thresh_hold and not re.match(d_pat, word):
            keys.append(word)
        else:
            # 如果是数字，直接视为值
            if re.match(d_pat, word):
                values.append(word)
            else:
                if len(word) > 10:  # 过长的视为文本
                    text.append(word)
                else:
                    values.append(word)  # 否则视为值

    keys_dict = defaultdict(list)
    for key in keys:
        keys_dict[len(key)].append(key)

    values_dict = defaultdict(list)
    for key in values:
        values_dict[len(key)].append(key)

    return keys_dict, values_dict, text, keys, values


def read_background(bg_dir):
    """读取背景及其标注文件"""
    for text_file in glob.iglob(os.path.join(bg_dir, "*.txt")):
        path, _ = os.path.split(text_file)
        with open(text_file, "r", encoding="utf-8") as file:
            for line in file:
                jpg, left, top, right, bottom, _ = line.split(";")
                bg_box = (int(left), int(top), int(right), int(bottom))
                bg_path = os.path.join(path, jpg)
                yield bg_path, bg_box
