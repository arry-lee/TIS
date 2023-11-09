"""
置换滤镜
"""
import os

import cv2
import numpy as np
from PIL import Image

from postprocessor.convert import as_array

BASEDIR = os.path.dirname(__file__)
TEXTURE_DIR = os.path.join(BASEDIR,'paper')
DEFAULT_TEXTURE = os.path.join(TEXTURE_DIR,'paper.jpeg')

def displace(text_layer,
             texture=DEFAULT_TEXTURE,
             ratio=5,
             mask_only=False):
    """
    模拟实现PS的置换滤镜，将文字层投射到纹理层上面
    :param texture: 纹理 RGB
    :param text_layer: 文字层 RGBA
    :param ratio: 最大的偏移半径
    :return: Image
    """
    texture = as_array(texture)
    text_layer = as_array(text_layer)
    
    rows, cols = text_layer.shape[:2]
    paper = cv2.resize(texture, (cols, rows))
    filter_img = cv2.cvtColor(paper, cv2.COLOR_BGR2GRAY)
    
    map_y = np.array([list(range(rows)) for _ in range(cols)], np.float32).T
    map_x = np.array([list(range(cols)) for _ in range(rows)], np.float32)
    # 最大偏移量为 ratio,将偏移范围约束到-5到5之间
    
    divide = 127 / ratio
    map_dx = (filter_img - 127) / divide
    map_dy = (filter_img - 127) / divide
    map_x = map_x + map_dx
    map_y = map_y + map_dy
    map_x = np.clip(map_x, 0, cols - 1).astype(np.float32)
    map_y = np.clip(map_y, 0, rows - 1).astype(np.float32)
    mask_text = cv2.remap(text_layer, map_x, map_y,
                          interpolation=cv2.INTER_LINEAR)
    mask = Image.fromarray(cv2.cvtColor(mask_text,cv2.COLOR_BGRA2RGBA))
    if mask_only:
        return mask
    paper = Image.fromarray(paper)
    paper.paste(mask, mask=mask)
    return paper
