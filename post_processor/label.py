# 处理标注方法
import cv2
import numpy as np


def log_label(fn, img, data):
    labels = data['label']
    points = data['points']
    with open(fn, 'w',encoding='utf-8') as f:
        for lno, label in enumerate(labels):
            x1, y1 = int(points[lno * 4][0]), int(points[lno * 4][1])
            x2, y2 = int(points[lno * 4 + 1][0]), int(points[lno * 4 + 1][1])
            x3, y3 = int(points[lno * 4 + 2][0]), int(points[lno * 4 + 2][1])
            x4, y4 = int(points[lno * 4 + 3][0]), int(points[lno * 4 + 3][1])
            line = ';'.join(map(str, [img, x1, y1, x2, y2, x3, y3, x4, y4, label]))
            f.write(line + '\n')


def show_label(data):
    labels = data['label']
    points = data['points']
    img = data['image']

    for lno, label in enumerate(labels):
        x1, y1 = int(points[lno * 4][0]), int(points[lno * 4][1])
        x2, y2 = int(points[lno * 4 + 1][0]), int(points[lno * 4 + 1][1])
        x3, y3 = int(points[lno * 4 + 2][0]), int(points[lno * 4 + 2][1])
        x4, y4 = int(points[lno * 4 + 3][0]), int(points[lno * 4 + 3][1])
        pts = np.array([[x1, y1], [x2, y2], [x3, y3], [x4, y4]], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(img, [pts], isClosed=True, color=(0, 255, 0))
    data['image'] = img
    return data