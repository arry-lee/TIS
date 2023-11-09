"""
  原理: 扩散滤镜的效果是局部混乱而整体有序，可在邻域中随机取值实现，
  这样在邻域中便是混乱的，而邻域间仍保持有序，从而保证了整体的有序。
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
import cv2
import numpy as np


def scan(image, offset=1, ksize=(3, 3)):
    """
    扫描扩散滤镜
    :param image: np.ndarray 原图
    :param offset: int 表示偏移值 越大越模糊
    :param ksize: tuple[int,int] 高斯模糊核 (3,3),(5,5),(7,7)
    :return: np.ndarray
    """
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, image = cv2.threshold(image, 125, 200, cv2.THRESH_BINARY)
    out = spread(image, offset)
    return cv2.cvtColor(cv2.blur(out, ksize), cv2.COLOR_GRAY2BGR)


def spread(image, offset=1):
    """
    扩散滤镜
    :param image: np.ndarray 原图
    :param offset: int 表示扩散偏移量 越大越模糊 一般取 1
    :return: np.ndarray
    """
    rows, cols = image.shape[:2]
    map_y = np.array([list(range(rows)) for _ in range(cols)], np.float32).T
    map_x = np.array([list(range(cols)) for _ in range(rows)], np.float32)
    map_ex = np.random.randint(-offset, offset, (rows, cols))
    map_ey = np.random.randint(-offset, offset, (rows, cols))
    map_x = map_x + map_ex
    map_y = map_y + map_ey
    map_x = np.clip(map_x, 0, cols - 1).astype(np.float32)
    map_y = np.clip(map_y, 0, rows - 1).astype(np.float32)
    out = cv2.remap(image, map_x, map_y, interpolation=cv2.INTER_LINEAR)
    return out
