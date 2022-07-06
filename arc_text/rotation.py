import cv2
import numpy as np


def rotate_bound(image, angle, borderValue=(0, 0, 0), mask=False, matrix=False):
    """旋转图片，扩展边界"""
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D((cX, cY), angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    # compute the new bounding dimensions of the image
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    # adjust the rotation matrix to take into account translation
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
    # perform the actual rotation and return the image
    out = cv2.warpAffine(image, M, (nW, nH), borderValue=borderValue)
    if not mask and not matrix:
        return out

    if mask is True:
        mask = np.ones((h, w), np.uint8) * 255
        mask = cv2.warpAffine(mask, M, (nW, nH), borderValue=0)
        if matrix:
            return out, mask, M
        else:
            return out, mask

    if matrix:
        return out, M


def rotate_points(points, matrix):
    """旋转原始点，得到新的点坐标"""
    points = np.array(points)
    h, w = points.shape
    nps = np.ones((h, 3), np.uint32)
    nps[:, :2] = points
    out = np.array(np.matmul(nps, matrix.T))
    return out


def rotate_data(data, angle=0, borderValue=(0, 0, 0)):
    """旋转一个字典图片"""
    assert isinstance(data, dict)
    data["image"], mask, M = rotate_bound(
        data["image"], angle=angle, borderValue=borderValue, mask=True, matrix=True
    )
    data["points"] = rotate_points(data["points"], M)
    if data.get("mask", None) is not None:
        data["mask"] = rotate_bound(data["mask"], angle=angle, borderValue=borderValue)
    else:
        data["mask"] = mask
    return data


if __name__ == "__main__":
    img = cv2.imread(r"E:\00IT\P\uniform\data\bank\006662781.jpg", 1)
    o = rotate_bound(img, 0.5)
    cv2.imshow("", o)
    cv2.imwrite("x.jpg", o)
    cv2.waitKey(0)
