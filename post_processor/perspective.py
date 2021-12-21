import cv2
import numpy as np


def perspective(img,ld=0.02,rd=0.02,borderValue=(0,0,0),mask=False,matrix=False):
    """透视变换并且填充背景
        假定下面两点是不动的,左上边点向右偏移 dx，右上点向左偏移 dy；
    """
    h, w = img.shape[:2]
    src = np.float32([(0, 0), (w, 0), (0, h), (w, h)])
    dst = np.float32([(w*ld, 0),(w-w*rd, 0), (0, h),(w, h)])
    M = cv2.getPerspectiveTransform(src, dst)
    out = cv2.warpPerspective(img, M, [w, h], borderValue=borderValue)
    if not mask and not matrix:
        return out
    if mask is True:
        mask = np.ones((h, w), np.uint8) * 255
        mask = cv2.warpPerspective(mask, M, [w, h], borderValue=0)
        if matrix:
            return out, mask, M
        else:
            return out, mask
    if matrix:
        return out, M


def _trans(points, M):
    points = np.array(points)
    h, w = points.shape
    nps = np.ones((h, 3), np.uint32)
    nps[:, :2] = points
    out = np.array(np.matmul(nps, M.T))
    return out


def perspective_points(points, M):
    """经过透视变化后的点坐标"""
    x = _trans(points, M)
    x[:, 0] = np.round(x[:, 0] // x[:, 2])
    x[:, 1] = np.round(x[:, 1] // x[:, 2])
    points = np.array(x[:, :2], np.uint32)
    return points



def perspective_data(data,ld=0.05,rd=0.05):
    assert isinstance(data,dict)

    data['image'],mask,M = perspective(data['image'],ld,rd,mask=True,matrix=True)
    data['points'] = perspective_points(data['points'],M)
    if data.get('mask',None) is not None:
        data['mask'] = perspective(data['mask'],ld,rd)
    else:
        data['mask'] = mask
    return data


if __name__ == '__main__':
    from rotation import rotate_bound
    from distortion import distortion
    img = cv2.imread(r"E:\00IT\P\uniform\data\bank\006662781.jpg",1)
    img = distortion(img,1,5)
    img = rotate_bound(img,1)
    o = perspective(img)
    cv2.imshow('',o)
    cv2.imwrite('x.jpg',o)
    cv2.waitKey(0)