"""
颜色聚类模块，减少图像的杂色
"""

import cv2
import numpy as np

from post_processor.deco import as_cv
from utils.cv_tools import cvshow


def reduce_color(img, num=3):
    """
    通过聚类将图像中的颜色简化为 num 种
    :param img: np.ndarray | path
    :param num: int color numbers
    :return: np.ndarray
    """
    img = as_cv(img)
    flat = np.float32(img.reshape((-1, 3)))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, label, center = cv2.kmeans(
        flat, num, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
    )
    # Now convert back into uint8, and make original image
    center = np.uint8(center)
    res = center[label.flatten()]
    res2 = res.reshape((img.shape))
    return res2


def split_color(img):
    """
    提取两个主色，前景色和背景色
    :param img: np.ndarray
    :return: tuple background and foreground
    """
    flat = np.float32(img.reshape((-1, 3)))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, __, center = cv2.kmeans(flat, 2, None, criteria, 10,
                              cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    return center[0], center[1]


def mean_color(colors):
    """平均色"""
    flat = np.float32(colors.reshape((-1, 3)))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, __, center = cv2.kmeans(flat, 1, None, criteria, 10,
                              cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    return center[0]


def most_color(colors):
    """最多的颜色"""
    return np.mean(colors)


def get_colormap(img):
    """重新着色"""
    img = reduce_color(img, 3)
    cmap = [None] * 256
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    for i in range(h):
        for j in range(w):
            cmap[gray[i, j]] = img[i, j, :]
    
    last_color = None
    
    for c in cmap:
        if c is not None:
            last_color = c
            break
    
    for idx, c in enumerate(cmap):
        if c is None:
            cmap[idx] = last_color
        else:
            last_color = c
    
    return cmap


def colormap(im, cmap):
    # im = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    h, w = im.shape
    out = np.zeros((h, w, 3), np.uint8)
    for i in range(h):
        for j in range(w):
            out[i, j] = cmap[im[i, j]]
    return out


if __name__ == '__main__':
    im = cv2.imread(r"E:\00IT\P\uniform\static\colormap\rb.jpg",
                    cv2.IMREAD_COLOR)
    im1 = cv2.imread(
        r"E:\00IT\P\uniform\multilang\output_data\form\cs\form_cs_00000000_1666863236.jpg")
    h, w = im1.shape[:2]
    
    gr = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gr, 125, 255, cv2.THRESH_BINARY_INV)
    pos0 = np.array(np.where(th == 0)).T
    pos1 = np.array(np.where(th != 0)).T
    bg = np.array([im[pos[0], pos[1]] for pos in pos0])
    fg = np.array([im[pos[0], pos[1]] for pos in pos1])
    
    # print(bg,fg)
    bgc = mean_color(bg)
    fgc = mean_color(fg)
    
    print(bgc, fgc)
    print(np.median(bg, axis=0), np.median(fg, axis=0))
    out = np.ones_like(im) * bgc
    for pos in pos1:
        out[pos[0], pos[1]] = fgc
    cvshow(out)
    
    # gr1 = cv2.cvtColor(im1,cv2.COLOR_BGR2GRAY)
    # _,th1 = cv2.threshold(gr1,128,255,cv2.THRESH_BINARY)
    # pos10 = np.array(np.where(th1==0)).T
    # pos11 = np.array(np.where(th1!=0)).T
    #
    # out = np.ones_like(im1)*255
    # # cvshow(th)
    # im = reduce_color(im,1)
    # cvshow(im)
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT,ksize=(7,7))
    # th = cv2.morphologyEx(th,cv2.MORPH_DILATE,kernel)
    # bg = cv2.inpaint(im,th,1,cv2.INPAINT_NS)
    # cv2.imwrite('msk.jpg',th)
    # cv2.imwrite('bg.jpg',bg)
    # # out = np.where(th1!=0,im)
    lastbg = (255, 255, 255)
    lastfg = (0, 0, 0)
    
    # cvshow(th)
    # cvshow(im)
    # for i in range(h):
    #     for j in range(w):
    #         if th1[i][j]==255 and th[i][j]==255:
    #             out[i][j] = im[i][j]
    #             lastbg = im[i][j]
    #         elif th1[i][j]==0 and th[i][j]==0:
    #             out[i][j] = im[i][j]
    #             # lastfg = im[i][j]
    #         elif th1[i][j]==255 and th[i][j]==0:
    #             out[i][j] = lastbg
    #             lastfg = im[i][j]
    #         else:
    #             # out[i][j] = lastfg
    #             lastbg = im[i][j]
    # # todo 相邻像素在原图上的位置也是相邻的
    # # 将pos0 和 pos10的坐标映射上
    # for index,p in enumerate(pos10):
    #     idx = int(index/(pos10.shape[0]-1)*(pos0.shape[0]-1))
    #     # idx = random.randint(0,pos0.shape[0]-1)
    #     x,y = pos0[idx]
    #     out[p[0],p[1]] = im[x,y]
    
    # for index,p in enumerate(pos11):
    #     idx = int(index/(pos11.shape[0]-1)*(pos1.shape[0]-1))
    #
    #     # idx = random.randint(0, pos1.shape[0]-1)
    #     x,y = pos1[idx]
    #     out[p[0], p[1]] = im[x, y]
    
    cv2.imwrite('x.jpg', out)
    
    # cmap = get_colormap(r"E:\00IT\P\uniform\static\colormap\rb.jpg")
    # # print(cmap.shape)
    # im = cv2.imread(r"E:\00IT\P\uniform\multilang\output_data\form\cs\form_cs_00000000_1666863236.jpg",cv2.IMREAD_GRAYSCALE)
    #
    # # b = cv2.applyColorMap(im,cmap[:,0])
    # # # print(cmap)
    # # cv2.imwrite('b.jpg',b)
    # #
    # # g = cv2.applyColorMap(im,cmap[:,1])
    # # # print(cmap)
    # # cv2.imwrite('g.jpg',g)
    # #
    # # r = cv2.applyColorMap(im,cmap[:,2])
    # # # print(cmap)
    # # cv2.imwrite('r.jpg',r)
    # #
    # # x = np.stack((b[:,:,0], g[:,:,0], r[:,:,0]), axis=2)
    # # # x = cv2.merge([b,g,r])
    # # #
    #
    # x = colormap(im,cmap)
    # cv2.imwrite('x.jpg',x)
