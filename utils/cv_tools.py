import cv2 as cv
import numpy as np
import os


def cvshow(img):
    if isinstance(img,str):
        img = cv.imread(img,cv.IMREAD_COLOR)
    cv.imshow('temp', img)
    cv.waitKey(0)
    cv.destroyAllWindows()


def test_on_dir(dir,func):
    assert os.path.isdir(dir)
    count = 0
    error = 0
    for img in os.listdir(dir):
        if img.endswith('jpg'):
            img = os.path.join(dir,img)
            try:
                func(img)
            except Exception as e:
                print(img,e)
                error += 1
            finally:
                count += 1
    score = 1 - error/count
    print('Exception:',error,'Total:',count,'Score:',score)
    return score

if __name__ == '__main__':
    img = cv.imread(r'E:\00IT\P\lama\image\tmp_mask.png',cv.IMREAD_UNCHANGED)
    print(img.shape)