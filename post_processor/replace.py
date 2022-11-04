"""所谓置换滤镜，就是将置换图中的像素点灰度值作为原图对应像素的移动距离，最后通过插值得到结果图。"""
# """
# for (int y = 0; y < pSrcBitmap->lHeight; y++)
# {
# 	alpha = 0.8f - (float)y / gradient_len;
# 	posy = ((float)y / pSrcBitmap->lHeight)*height;
# 	for (int x = 0; x < pSrcBitmap->lWidth; x++, pSrcData += 4)
# 	{
# 		posx = ((float)x / pSrcBitmap->lWidth)*width;
# 		BilinearInterGray(noise_data0, posx, posy, width, height, &noise_val0);
# 		BilinearInterGray(noise_data1, posx, posy, width, height, &noise_val1);
#
# 		float offset_x = (128 - noise_val0)*hor_ratio*alpha;
# 		float offset_y = (128 - noise_val1)*ver_ratio*alpha;
# 		BilinearInterRGB(data_copy, x + offset_x, y + offset_y, pSrcBitmap->lWidth, pSrcBitmap->lHeight, &bval, &gval, &rval);
# 		pSrcData[AXJ_BLUE] = bval;
# 		pSrcData[AXJ_GREEN] = gval;
# 		pSrcData[AXJ_RED] = rval;
# 	}
# }
# """
import cv2
import numpy as np
from PIL import Image

from .deco import as_cv, p2c


def replacement(text_layer,
                texture=r"E:\00IT\P\uniform\multilang\temp\paper.jpeg",
                ratio=5):
    """
    模拟实现PS的置换滤镜，将文字层投射到纹理层上面
    :param texture: 纹理 RGB
    :param text_layer: 文字层 RGBA
    :param ratio: 最大的偏移半径
    :return: Image
    """
    texture = as_cv(texture)
    text_layer = as_cv(text_layer)
    
    rows, cols = text_layer.shape[:2]
    paper = cv2.resize(texture, (cols, rows))
    filter_img = cv2.cvtColor(paper, cv2.COLOR_BGR2GRAY)
    
    # max_ = np.max(filter_img)
    # min_ = np.min(filter_img)
    # filter_img = filter_img*255/(max_-min_)
    
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
    mask = Image.fromarray(mask_text)
    paper = Image.fromarray(paper)
    paper.paste(mask, mask=mask)
    return np.asarray(paper, np.uint8)


if __name__ == '__main__':
    p = replacement(
        r"E:\00IT\P\uniform\multilang\templates\newspaper\4e69845969baca1c49a96375bfabdaa9-1.png")
    p.save('f.jpg')
