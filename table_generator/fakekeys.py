import os
import re
import glob
from collections import Counter, defaultdict

"""
1.将所有的词条准备好
2.按长度分组,长度小于6的视为 key 且不是纯数字，出现次数大于2的
3.长度大于20 的为multitext
4.只出现1次的视为值
"""


def key_value_generator(basedir, key_thresh_hold=None):
    """
    basedir 存放标注数据的文件夹
    key_thresh_hold 视为键的数量阈值
    """
    texts = glob.glob(os.path.join(basedir, "*.txt"))
    # print(texts)
    counter = Counter()
    for text in texts:
        with open(text, "r", encoding="gbk", errors="ignore") as f:
            for line in f:
                word = line.strip().split("@")[-1]
                if len(word) > 1:
                    counter.update({word: 1})

    keys = []
    values = []
    text = []
    # print(counter)
    if key_thresh_hold is None:
        key_thresh_hold = counter.most_common(1)[0][1] // 2

    d_pat = re.compile(".*\d.*")  # 任何纯数字的
    for word, c in counter.items():
        # 重复数量过多而且不是数字，视为键
        if c > key_thresh_hold and not re.match(d_pat, word):
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
    bgs = glob.iglob(os.path.join(bg_dir, "*.txt"))
    for ino, text_file in enumerate(bgs):
        p, fn = os.path.split(text_file)
        with open(text_file, "r", encoding="utf-8") as f2:
            for line in f2:
                jpg, l, t, r, b, label = line.split(";")
                box = (int(l), int(t), int(r), int(b))
                bg = os.path.join(p, jpg)
                yield bg, box
