import glob
import cv2
from PIL import Image
import numpy as np


def p2c(image):
    return cv2.cvtColor(np.asarray(image, np.uint8), cv2.COLOR_RGB2BGR)


def yuepu(name):
    names = glob.glob(name + "*.jpg")
    ims = []
    for fp in names:
        im = Image.open(fp).convert("L").point(lambda x: x * 1.5)
        box = (0, 300, im.width, im.height - 150)
        ims.append(p2c(im.crop(box)))
    vim = np.hstack(ims)
    cv2.imwrite("h" + name + ".jpg", vim)
    return vim


if __name__ == "__main__":
    yuepu("my")
