import glob
import os
import random

from faker.providers import BaseProvider

from arc_text.arctext import ArcText, StraightText
from arc_text.layout import HorLayout, VerLayout
from picsum import rand_image

import faker


class Provider(BaseProvider):
    font_dir = r"C:\Users\dell\AppData\Local\Microsoft\Windows\Fonts"
    # font_list = glob.glob(os.path.join(font_dir, '*ttf'))

    font_list = [
        "simfang.ttf",
        "simhei.ttf",
        "simkai.ttf",
        "STCAIYUN.TTF",
        "SIMYOU.TTF",
        "SIMLI.TTF",
        "STXINGKA.TTF",
    ]

    f = faker.Faker("zh_CN")

    def background(self, w, h):
        return rand_image(w, h)

    def font_path(self):
        return self.random_element(self.font_list)

    def font_size(self, minsize=32, maxsize=50):
        return random.randint(minsize, maxsize)

    def color(self):
        return (255, 255, 255, 255)

    def radius(self, min=100, max=500):
        return random.randint(min, max)

    def close_ratio(self):
        return 0.7

    def rotation(self):
        return random.randint(-45, 45)

    def hor(self, ratio=0.3):
        return random.random() < ratio

    def ver(self, ratio=0.2):
        return random.random() < ratio

    def perspective(self, ratio=0.5):
        return random.random() < ratio

    def clockwise(self, ratio=0.5):
        return random.random() < ratio

    def arctext(self):
        return ArcText(
            self.f.sentence()[:-1],
            self.font_path(),
            self.font_size(),
            self.color(),
            self.radius(),
            self.clockwise(),
            self.close_ratio(),
            False,
            self.rotation(),
            self.hor(),
        )

    def straighttext(self):
        return StraightText(
            self.f.sentence()[:-1],
            self.font_path(),
            self.font_size(),
            self.color(),
            self.rotation(),
            self.ver(),
            self.perspective(),
        )

    def text(self):
        if random.random() < 0.5:
            return self.arctext()
        else:
            return self.straighttext()

    def layouts(self, max_rows=4, max_cols=3):
        rows = random.randint(2, max_rows)
        vs = []
        for i in range(rows):
            col = random.randint(2, max_cols)
            hs = []
            for _ in range(col):
                hs.append(self.text())
            vs.append(HorLayout(hs))
        return VerLayout(vs)

    def image(self):
        lo = self.layouts()
        data = lo.get_image()
        im = data["image"]
        w, h = im.size
        bg = self.background(w, h)
        bg.paste(im, (0, 0), im)
        data["image"] = bg
        return data


if __name__ == "__main__":
    f = faker.Faker(providers=["provider"])
    im = f.image()["image"]
    im.save("t.jpg")
