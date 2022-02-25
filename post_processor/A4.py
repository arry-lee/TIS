import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from post_processor._post_processor import rotate_bound, keepdata

w_mm = 210  # A4 的毫米尺寸
h_mm = 279
DIP = 4  # 每毫米像素数量
WIDTH, HEIGHT = w_mm * DIP, h_mm * DIP

white = (244, 244, 244)

left,right,top,bottom = 25*DIP,25*DIP,20*DIP,20*DIP

texture_dir = '../static/paper/'

class Paper(object):
    """纸张模拟器"""
    def __init__(self, width=None,type='A4', texture=None, color=(255, 255, 255), dip=4, direction='v',offset_p=None,offset=20):
        self.type = type
        self.direction = direction
        self.texture =texture
        self.color = color
        self.offset = offset

        if self.type.upper() == 'A4':
            self.width_mm = 210
            self.height_mm = 279
        if self.direction == 'h':
            self.width_mm,self.height_mm = self.height_mm,self.width_mm
        if not width:
            self.dip = dip
            self.width = self.dip * self.width_mm
            self.height = self.dip * self.height_mm
        else:
            self.width = width
            self.dip = width//self.width_mm
            self.height = self.dip*self.height_mm

        self.size = (self.width,self.height)

        if self.texture:
            self._image = Image.open(self.texture).resize(self.size)
        else:
            # _image = np.random.randint(244,255,(self.height,self.width,3),np.uint8)
            # self._image = Image.fromarray(_image)
            self._image = Image.new('RGB',self.size,self.color)
        #
        self._draw = ImageDraw.Draw(self._image)
        if offset_p is not None:
            offset = offset_p//self.dip

        self.pad = (offset * self.dip, offset * self.dip, offset * self.dip, offset * self.dip)
        self._box = (offset * self.dip, offset * self.dip, self.width-offset * self.dip, self.height-offset * self.dip)
        self.header_box = (0, 0,self.width, offset * self.dip)
        self.footer_box = (0, self.height-offset * self.dip, self.width,self.height)


    @property
    def image(self):
        # self._draw.rectangle(self._box,outline='black',width=4)
        return self._image

    def set_header(self,text,font,align='c',line=True):
        xy = self.width//2,self.header_box[3]//2
        self._draw.line((0, 10 * DIP)+(self.width,10 * DIP),fill=(0,0,0),width=2)
        self._draw.text(xy,text,fill='black',font=font,anchor='mm')



    @property
    def box(self):
        return self._box

    @box.setter
    def box(self,value):
        if isinstance(value, (tuple, list)) and len(value)==4:
            self.left,self.top,self.right,self.bottom = value
            self._box = (self.left,self.top,self.width-self.right,self.height-self.bottom)



# a4 = Paper(color=(244,244,244))
# # a4.image.save(os.path.join(texture_dir,'texture02.jpg'))
# a4.image.show()



def fitwidth(image):
    h, w = image.shape[:2]
    H = int(WIDTH / w * h)
    W = WIDTH
    return cv2.resize(image, (W, H))


def add_a4(image):
    img = fitwidth(image)
    h, w = img.shape[:2]
    assert w == WIDTH
    out = np.ones((HEIGHT, WIDTH, 3), np.uint8) * 244
    out[:h, :] = img[:h, :]
    return out


@keepdata
def add_corner(image, type='fold'):
    if type == 'fold':
        corner = cv2.imread('../static/paper/corner_fd.jpg')
    else:
        corner = cv2.imread('../static/paper/corner_br.jpg')

    out = add_a4(image)
    h, w = corner.shape[:2]
    out[HEIGHT - h:, WIDTH - w:] = corner
    return out




# 15952000282
