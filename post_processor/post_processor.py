# 后处理效果
# 一个后处理函数，第一个参数必须为str or PIL.IMAGE,输出必须是PIL.IMAGE
import os
import random

import cv2 as cv
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from post_processor.color_reducer import minimize_color

def p2c(image):
    return cv.cvtColor(np.array(image, np.uint8), cv.COLOR_RGB2BGR)


def c2p(image):
    return Image.fromarray(cv.cvtColor(image, cv.COLOR_BGR2RGB))


def as_pillow(img):
    if isinstance(img, str):
        return Image.open(img)
    elif isinstance(img, np.ndarray):
        return c2p(img)
    else:
        return img


def imageit(func):
    """将输入包装成cv格式"""
    def wrap(img, *args, **kwargs):
        if isinstance(img, str):
            img = cv.imread(img, cv.IMREAD_COLOR)
        elif isinstance(img, Image.Image):
            img = cv.cvtColor(np.array(img), cv.COLOR_RGB2BGR)
        else:
            pass
        res = func(img, *args, **kwargs)
        return res
    return wrap


def keepdata(func):
    """将处理器函数包装成可以处理字典的,任何输入转换为cv,输出为cv"""
    def wrap(img, *args, **kwargs):
        if isinstance(img, str):
            oimg = cv.imread(img, cv.IMREAD_COLOR)
        elif isinstance(img, Image.Image):
            oimg = cv.cvtColor(np.array(img), cv.COLOR_RGB2BGR)
        elif isinstance(img, dict):
            oimg = img['image']
        else:
            oimg = img

        res = func(oimg, *args, **kwargs)

        if isinstance(img, dict):
            if isinstance(res, Image.Image):
                img['image'] = p2c(res)
            else:
                img['image'] = res
            return img
        else:
            if isinstance(res, Image.Image):
                img['image'] = p2c(res)
            else:
                img['image'] = res
    return wrap


def trans(points, M):
    points = np.array(points)
    h, w = points.shape
    nps = np.ones((h, 3), np.uint32)
    nps[:, :2] = points
    out = np.array(np.matmul(nps, M.T))
    return out


def pers_trans(points, M):
    x = trans(points, M)
    # print(x)
    x[:, 0] = np.round(x[:, 0] // x[:, 2])
    x[:, 1] = np.round(x[:, 1] // x[:, 2])
    points = np.array(x[:, :2], np.uint32)
    return points


@imageit
def rotate_bound(image, angle, borderValue=(255, 255, 255)):
    """旋转素材"""
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
    M = cv.getRotationMatrix2D((cX, cY), angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    # compute the new bounding dimensions of the image
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    # adjust the rotation matrix to take into account translation
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
    # perform the actual rotation and return the image
    # point = [[216, 28], [216, 28]]
    # point = trans(point,M)
    return cv.warpAffine(image, M, (nW, nH), borderValue=borderValue)


def rotate_bound_data(data, angle, borderValue=(255, 255, 255)):
    """旋转素材"""
    image = data['image']
    points = data['points']
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
    M = cv.getRotationMatrix2D((cX, cY), angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    # compute the new bounding dimensions of the image
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    # adjust the rotation matrix to take into account translation
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
    # perform the actual rotation and return the image
    # point = [[216, 28], [216, 28]]
    # point = trans(point,M)
    data['points'] = trans(points, M)
    data['image'] = cv.warpAffine(image, M, (nW, nH), borderValue=borderValue)
    return data




@keepdata
def add_pollution(img, xy=None, angle=None, seal_p='./static/dirty/youmo.png'):
    """ 添加污染效果

    img：原图
    xy: 位置
    angle: 角度
    seal: 文件或污染图
    """
    img = as_pillow(img)
    w, h = img.size
    if xy is None:
        xy = random.randint(0,  3 * w // 4), random.randint(0,  3 * h // 4)
    if angle is None:
        angle = random.randint(0, 45)

    seal = cv.imread(seal_p, cv.IMREAD_COLOR)
    seal = rotate_bound(seal, angle)
    seal = Image.fromarray(
        cv.cvtColor(minimize_color(seal, 2), cv.COLOR_BGR2RGB))
    mask = seal.convert('L').point(lambda x: 0 if x > 200 else x)
    img.paste(seal, xy, mask=mask)
    return img


def shouhui(im):
    a = np.array(as_pillow(im).convert('L')).astype('float')
    depth = 8
    grad = np.gradient(a)
    grad_x,grad_y = grad
    grad_x = grad_x*depth/100
    grad_y = grad_y*depth/100

    vec_el = np.pi/2.2   # 光源仰角
    vec_az = np.pi/4     # 光源方位角

    dx = np.cos(vec_el)*np.cos(vec_az)  # x投影
    dy = np.cos(vec_el)*np.sin(vec_az)
    dz = np.sin(vec_el)

    A = np.sqrt(grad_x**2+grad_y*2+1)
    uni_x = grad_x/A
    uni_y = grad_y/A
    uni_z = 1/A

    b = 255*(dx*uni_x+dy*uni_y+dz*uni_z) # 梯度与光源相互作用
    b = b.clip(0,255)

    return b.astype('uint8')


def signature(text):
    font = r'E:\00IT\P\PaddleOCR\doc\fonts\shouxie.ttf'
    ft = ImageFont.truetype(font, size=45, encoding='utf-8')
    size = ft.getsize(text)
    bg = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(bg)
    draw.text((0, 0), text, fill='black', font=ft)
    return bg


def add_signature(img, text, xy, angle=0):
    """增加签名"""
    img = as_pillow(img)
    text = signature(text)
    text = np.array(text)
    if angle:
        text = rotate_bound(text, angle)
    text = Image.fromarray(text)
    mask = text.split()[0].point(lambda x: 0 if x > 125 else 255)
    img.paste(text, xy, mask=mask)
    return img


def handwrite(data, sign="<s>"):
    # 将指定部分转换为手写体
    img = c2p(data['image'])
    font = r'E:\00IT\P\PaddleOCR\doc\fonts\shouxie.ttf'

    draw = ImageDraw.Draw(img)

    for box, label in zip(data['boxes'], data['label']):
        bgc = img.getpixel((box[0] - 1, box[1] - 1))
        bg = Image.new('RGB', (box[2] - box[0], box[3] - box[1]), bgc)
        # draw = ImageDraw.Draw(bg)
        if label[0] == '@' and '<s>' in label:
            fontsize = box[3] - box[1] + 5
            img.paste(bg, (box[0], box[1]))
            ft = ImageFont.truetype(font, size=fontsize, encoding='utf-8')
            draw.text((box[0], box[1]), label[1:-3], fill='black', font=ft)

    data['image'] = p2c(img)

    return data


def empty(data):
    # 将指定部分转换为手写体
    img = c2p(data['image'])
    draw = ImageDraw.Draw(img)
    for box, label in zip(data['boxes'], data['label']):
        bgc = img.getpixel((box[0] - 1, box[1] - 1))
        bg = Image.new('RGB', (box[2] - box[0], box[3] - box[1]), bgc)
        # draw = ImageDraw.Draw(bg)
        if label[0] == '@':
            img.paste(bg, (box[0], box[1]))

    data['image'] = p2c(img)

    return data


def del_vline(data):
    """后处理删除竖线"""
    img = c2p(data['image'])
    draw = ImageDraw.Draw(img)
    for box, label in zip(data['boxes'], data['label']):
        if label[-1] == '@':
            draw.rectangle(box, outline='white', width=2)

    for box, label in zip(data['boxes'], data['label']):
        if label[-1] == '@':
            draw.line((box[0], box[1]) + (box[2], box[1]), fill='black',
                      width=2)
            # draw.line((box[0],box[3])+(box[2],box[3]),fill='black',width=2)
    data['image'] = p2c(img)
    return data


def add_box_bg(data):
    """给某些单元格加背景"""
    img = data['image']
    for box, label in zip(data['boxes'], data['label']):
        r = (box[3] - box[1]) / (box[2] - box[0])
        if r > 0.6 and label[-1] == '@':
            img[box[1]:box[3], box[0]:box[2]] = np.array(
                0.8 * img[box[1]:box[3], box[0]:box[2]], np.uint8)
    data['image'] = img
    return data


@imageit
def perspective(img, background='./data/bg_wood.jpg'):
    """透视变换并且填充背景
    """
    h, w = img.shape[:2]
    bg = cv.imread(background, 1)
    nbg = cv.resize(bg, (w + 200, h + 200))

    nbg[100:h + 100, 100:w + 100] = img

    h, w = nbg.shape[:2]
    lt = (100, 0)
    rt = (w - 50, 0)
    lb = (0, h)
    rb = (w, h)

    src = np.float32([(0, 0), (w, 0), (0, h), (w, h)])
    dst = np.float32([lt, rt, lb, rb])
    M = cv.getPerspectiveTransform(src, dst)
    nim = cv.warpPerspective(nbg, M, [w, h], borderValue=(255, 255, 255))

    nimg = nim[:, 100:w - 50]

    return c2p(nimg)


def perspective_and_rotate_on_background(data, border_dir=r'static/texture'):
    """在背景上旋转并融合"""
    angle = random.randint(-2, 2)
    mask = np.ones(data['image'].shape[:2], np.uint8) * 255
    data = rotate_bound_data(data, angle)  # 一次坐标变换

    img = data['image']
    point = data['points']
    mask = rotate_bound(mask, angle, 0)
    mask = Image.fromarray(mask)

    bg = cv.imread(random_source(border_dir), 1)

    h, w = img.shape[:2]
    nbg = cv.resize(bg, (w + 200, h + 200))

    out = c2p(nbg)
    out.paste(c2p(img), (100, 100), mask=mask)  # 二次坐标变换
    point = point + 100

    w, h = out.size
    lt = (50, 0)
    rt = (w - 50, 0)
    lb = (0, h)
    rb = (w, h)
    src = np.float32([(0, 0), (w, 0), (0, h), (w, h)])
    dst = np.float32([lt, rt, lb, rb])
    M = cv.getPerspectiveTransform(src, dst)  # 三次坐标变换
    # print(M)
    # print(M.shape,point.shape)

    point = pers_trans(point, M)
    out = cv.warpPerspective(p2c(out), M, [w, h], borderValue=(255, 255, 255))

    point[:, 0] = point[:, 0] - 50
    data['image'] = out[:, 50:w - 50]
    data['points'] = point
    return data  # 四次坐标变换


@imageit
def rotate_on_background(img,border_dir=r'E:\00IT\P\PaddleOCR\ppotr\static\border'):
    """在背景上旋转并融合"""
    angle = random.randint(-10, 15)
    mask = np.ones(img.shape[:2], np.uint8) * 255

    img = rotate_bound(img, angle)
    mask = rotate_bound(mask, angle, 0)
    mask = Image.fromarray(mask)

    bg = cv.imread(random_source(border_dir), 1)

    h, w = img.shape[:2]
    nbg = cv.resize(bg, (w + 200, h + 200))

    out = c2p(nbg)
    out.paste(c2p(img), (100, 100), mask=mask)
    return out



def add_border(image,border_dir=r'E:\00IT\P\uniform\static\texture'):
    img = as_pillow(image)
    h, w = image.shape[:2]
    bg = as_pillow(random_source(border_dir)).resize((w,h))
    mask = img.convert('L').point(lambda x: 0 if x == 0 else 255)
    bg.paste(img,(0,0),mask=mask)
    return bg


def random_source(dir):
    return os.path.join(dir, random.choice(list(os.listdir(dir))))


def add_background(bg, data):
    img = c2p(data['image'])
    bg = as_pillow(bg)
    mask = img.convert('L').point(lambda x: 255 if x < 250 else 0)
    bg.paste(img, (10, 10), mask=mask)
    bg.show()
