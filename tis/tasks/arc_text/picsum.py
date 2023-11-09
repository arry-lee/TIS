import io

import requests
from PIL import Image

headers = {
    "Connection"               : "keep-alive",
    "Cache-Control"            : "max-age=0",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent"               : "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36",
    "Accept"                   : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding"          : "gzip, deflate, br",
    "Accept-Language"          : "zh-CN,zh;q=0.9,en;q=0.8",
}


def randimg(w, h):
    return "https://picsum.photos/%d/%d" % (w, h)


def get_img(img_url):
    response = requests.get(img_url, headers=headers)
    return response.content


def rand_image(w, h):
    return Image.open(io.BytesIO(get_img(randimg(w, h))))


def rand_person():
    return Image.open(
        io.BytesIO(get_img('https://thispersondoesnotexist.com/')))
