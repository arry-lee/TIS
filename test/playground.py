import io

import pyglet
import requests
from pyglet import shapes
from pyglet.window import key, mouse
from collections import deque


def randimg(w, h):
    return "https://picsum.photos/%d/%d" % (w, h)


def get_img(img_url):
    headers = {
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    response = requests.get(img_url, headers=headers)
    return response.content


# kitten_stream = open('kitten.png', 'rb')
# kitten = pyglet.image.load('kitten.png', file=kitten_stream)

window = pyglet.window.Window(
    resizable=True, caption="CMD", style=pyglet.window.Window.WINDOW_STYLE_DEFAULT
)

image = pyglet.image.load(
    "tmp.jpg", file=io.BytesIO(get_img(randimg(*window.get_size())))
)

label = pyglet.text.Label(
    "你好",
    font_name="Times New Roman",
    font_size=36,
    x=0,
    y=window.height,
    anchor_x="left",
    anchor_y="top",
)

circle = shapes.Circle(x=20, y=20, radius=20, color=(50, 225, 30))
circle.opacity = 120
circle.anchor_position = 50, 25


@window.event
def on_draw():
    window.clear()
    # image.blit(0,0)
    # label.draw()


@window.event
def on_key_press(symbol, modifiers):
    label.text = str(chr(symbol))
    # label.insert_text()
    if symbol == key.A:
        print('The "A" key was pressed.')
    elif symbol == key.LEFT:
        print("The left arrow key was pressed.")
    elif symbol == key.ENTER:
        global image
        image = pyglet.image.load(
            "tmp.jpg", file=io.BytesIO(get_img(randimg(*window.get_size())))
        )
        print("The enter key was pressed.")


@window.event
def on_mouse_press(x, y, button, modifiers):
    if button == mouse.LEFT:
        print("The left mouse button was pressed.")


event_logger = pyglet.window.event.WindowEventLogger()
window.push_handlers(event_logger)

pyglet.app.run()
