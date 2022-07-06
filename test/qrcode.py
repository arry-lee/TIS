import cv2
import numpy as np
from cv_tools import cvshow

im = cv2.imread("sqr.png", cv2.IMREAD_GRAYSCALE)

w, h = im.shape
# print(im)
white = np.ones(im.shape, np.uint8) * 255

step = 7
char = np.ones((step, step), np.uint8) * 100
blank = np.ones((step, step), np.uint8) * 255
black = np.zeros((step, step), np.uint8)

for i in range(40):
    for j in range(40):
        print(im[j * step : j * step + step, i * step : i * step + step])
        if np.mean(im[j * step : j * step + step, i * step : i * step + step]) < 128:
            white[j * step : j * step + step, i * step : i * step + step] = char
cvshow(im)
