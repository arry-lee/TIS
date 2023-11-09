"""
添加背景
"""
import cv2
import numpy as np

from postprocessor.convert import as_array, as_image, c2p, p2c


def add_background(image, background, offset=0, mask=None):
    """
    添加背景
    :param image: 原图
    :param background: 背景图
    :param offset: 偏移量
    :param mask: 蒙版
    :return: np.ndarray
    """
    # print(image)
    # assert image.mode == 'RGBA'
    img = as_image(image)
    width,height = img.size
    height += offset * 2
    width += offset * 2
    back = as_image(background).resize((width, height))
    if mask is not None:
        mask = as_image(mask).convert("L")
    if img.mode == 'RGBA':
        mask = img.getchannel('A')
    back.paste(img, (offset, offset), mask=mask)
    return p2c(back)




def add_background_data(data, background, offset):
    """
    添加背景同时修改标注
    :param data: dict 标注字典
    :param background: 背景图
    :param offset: 偏移量
    :return: dict 新标注字典
    """
    assert isinstance(data, dict)
    mask = data.get("mask", None)
    data["image"] = add_background(data["image"], background, offset, mask=mask)
    data["points"] = np.array(data["points"]) + offset
    return data


def add_to_paper(data, paper):
    """
    添加到纸张上
    :param data: dict 标注字典
    :param paper: Paper
    :return: dict 新标注字典
    """
    img = paper.image.copy()
    pos = paper.pad[0], paper.pad[1]
    img.paste(c2p(data["image"]), pos)
    data["image"] = p2c(img)
    data["points"] = np.array(data["points"]) + np.array(pos)
    return data


def get_background(img, thresh=128, ksize=(3, 3), iterations=2,
                   inpaint_radius=5):
    """
    移除图像中的文字，获取单纯的背景
    :param img: 图像
    :param thresh: 二值化的阈值
    :param ksize: 膨胀操作的核尺寸
    :param iterations: 膨胀操作的迭代次数
    :param inpaint_radius: 修复操作的半径
    :return: 背景图像
    """
    img = as_array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones(ksize, dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations)  # 膨胀
    # mask = cv2.erode(mask, kernel, iterations=1) #腐蚀
    out = cv2.inpaint(img, mask, inpaint_radius, cv2.INPAINT_TELEA)
    cv2.imwrite("mask.jpg", mask)
    cv2.imwrite("bg.jpg", out)
    return out
