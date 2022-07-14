# 原理: 扩散滤镜的效果是局部混乱而整体有序，可在邻域中随机取值实现，
# 这样在邻域中便是混乱的，而邻域间仍保持有序，从而保证了整体的有序。

"""
　１）输入文字。注意，不要在字体面板中选择任何消除字体的效果，默认为“无”。
　２）删格化图层。并把图层改名为L1。
　３）Ctrl+J复制一个新图层，起名为L2。
　４）选择L2图层，滤镜->风格化->扩散，选择“变亮优先”，确定。
　５）滤镜->模糊->高斯模糊，半径设为0.3，确定。
　６）将当前层不透明度设为60%。
　７）选择L1图层，滤镜->风格化->扩散，选择“变暗优先”，确定。
　８）将当前层不透明度设为60%。
　９）将两个图层合并。
　１０）再次选择滤镜->风格化->扩散，选择“变暗优先”，确定。
　１１）然后，滤镜->模糊->模糊。
　１２）酌情调整色相/饱和度，完成。
"""
import random

import cv2
import numpy as np


def scan(img, offset=1, ksize=(3, 3)):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    out = np.zeros_like(img)
    rows, cols = img.shape[:2]
    for i in range(rows):
        offU = i - offset if i - offset >= 0 else 0
        offD = i + offset if i + offset <= rows - 1 else rows - 1
        for j in range(cols):
            offL = j - offset if j - offset >= 0 else 0
            offR = j + offset if j + offset <= cols else cols - 1
            idxX = int(random.uniform(offL, offR))
            idxY = int(random.uniform(offU, offD))
            out[i, j] = img[idxY, idxX]
    o = cv2.blur(out, ksize)
    return o
