import io
import os
import os
import random
from string import digits, punctuation, ascii_letters

import requests
from PIL import Image
from faker.providers.lorem import Provider as BaseProvider

from multifaker.providers.table import Provider as TableProvider


def datelike(d):
    if d in "0129":
        return d
    return random.choice(digits)


class Provider(BaseProvider, TableProvider):
    """Implement default lorem provider for Faker.

    .. important::
       The default locale of the lorem provider is ``la``. When using a locale
       without a localized lorem provider, the ``la`` lorem provider will be
       used, so generated words will be in pseudo-Latin. The locale used for
       the standard provider docs was ``en_US``, and ``en_US`` has a localized
       lorem provider which is why the samples here show words in American
       English.
    """

    word_connector = " "
    sentence_punctuation = "."
    font_list = [
        "ANTQUAB",
        "ANTQUABI",
        "ANTQUAI",
        "arial",
        "arialbd",
        "arialbi",
        "ariali",
        "arialuni",
        "ARIALN",
        "ARIALNB",
        "ARIALNBI",
        "ARIALNI",
        "ariblk",
        "bahnschrift",
        "BKANT",
        "BOOKOS",
        "BOOKOSB",
        "BOOKOSBI",
        "BOOKOSI",
        "calibri",
        "calibrib",
        "calibrii",
        "calibril",
        "calibrili",
        "calibriz",
        "cambriab",
        "cambriai",
        "cambriaz",
        "Candara",
        "Candarab",
        "Candarai",
        "Candaral",
        "Candarali",
        "Candaraz",
        "CENTURY",
        "CENSCBK",
        "GARA",
        "GARABD",
        "GARAIT",
        "georgia",
        "georgiab",
        "georgiai",
        "georgiaz",
        "gothicb",
        "gothicbi",
        "impact",
        "SCHLBKB",
        "SCHLBKBI",
        "SCHLBKI",
        "times",
        "timesbd",
        "timesbi",
        "timesi",
    ]
    sign_font = r"E:\00IT\P\uniform\static\fonts\Sudestada.ttf"
    base_images_dir = r"E:\00IT\P\uniform\multispider\images"
    image_list = []

    def word_fontlike(self, font, length):
        keys = list(self.word_map.keys())
        keys.sort(reverse=True)
        for key in keys:
            word = self.word_map.get(key)[0]
            if font.getlength(word) > length:
                continue
            else:
                break
        word = self.random_element(self.word_map.get(key))
        return word

    def sentence_fontlike(self, font, length):
        """构造相同长度的句子"""
        # keys = list(self.word_map.keys())
        # keys.sort(reverse=True)

        size = font.size

        if length < size:
            return ""
        # self.word_map(key)
        # 随机选个单词
        word = self.words(1)[0]  # self.word_fontlike(font, length)
        # print(word)
        # return word
        if length - size * 2 <= font.getlength(word) <= length:
            return word

        if font.getlength(word) > length - size:
            while font.getlength(word) > length:
                # print('-')
                word = word[:-1]
                if not word:
                    return ""
            # print(word)
            return word

        if font.getlength(word) < length - 2 * size:
            # word = self.words(1)[0]

            return (
                word
                + " "
                + self.sentence_fontlike(font, length - font.getlength(word + " "))
            )
        # return ''

    def wordlike(self, word, exact=True):
        """选择相似长度的词"""
        if not exact:
            if len(word) <= 4:
                length = len(word)
            else:
                length = len(word) + random.randint(-2, 0)
        else:
            length = len(word)
        try:
            one = self.random_element(self.word_map[length])
        except IndexError:
            one = self.words(1)[0]
        if not one.strip():
            return word

        if word.istitle():
            return one.title()
        if word.isupper():
            return one.upper()
        if word.islower():
            return one.lower()
        return one

    def sentence_like(self, sentence, exact=True, keep_ascii=False):
        """构建在长度和结构上都相似的句子
        保持标点符合和数字不变
        """
        out = []
        word = ""
        if keep_ascii:
            signs = punctuation + ascii_letters + " " + digits
        else:
            signs = punctuation + digits + " "

        for char in sentence:
            if char in signs:
                if word:
                    out.append(word)
                word = ""
                out.append(char)
            else:
                word += char
        if word:
            out.append(word)
        words = []
        for char in out:
            if char in digits:
                words.append(datelike(char))
            elif char in signs:
                words.append(char)
            else:
                words.append(self.wordlike(char, exact))
        return "".join(words)

    # def word(self):
    def words(self, nb=3, ext_word_list=None, unique=False):
        """Generate a tuple of words.

        The ``nb`` argument controls the number of words in the resulting list,
        and if ``ext_word_list`` is provided, words from that list will be used
        instead of those from the locale provider's built-in word list.

        If ``unique`` is ``True``, this method will return a list containing
        unique words. Under the hood, |random_sample| will be used for sampling
        without replacement. If ``unique`` is ``False``, |random_choices| is
        used instead, and the list returned may contain duplicates.

        .. warning::
           Depending on the length of a locale provider's built-in word list or
           on the length of ``ext_word_list`` if provided, a large ``nb`` can
           exhaust said lists if ``unique`` is ``True``, raising an exception.

        :sample:
        :sample: nb=5
        :sample: nb=5, ext_word_list=['abc', 'def', 'ghi', 'jkl']
        :sample: nb=4, ext_word_list=['abc', 'def', 'ghi', 'jkl'], unique=True
        """
        word_list = ext_word_list if ext_word_list else self.word_list
        length = len(word_list) - 1
        return [word_list[random.randint(0, length)].strip() for _ in range(nb)]
        # 就这一项优化速度提高几百倍,random_choices 非常慢
        # if unique:
        #     return [word.strip() for word in
        #             self.random_sample(word_list, length=nb)]
        # return [word.strip() for word in
        #         self.random_choices(word_list, length=nb)]

    def font(self, mode=None):
        """
        各个语言可用字体
        :param mode: sign 手写 b 粗体 i 斜体
        :return: path
        """
        if mode == "sign":
            return self.sign_font

        if mode == "n":
            normal_fonts = [f for f in self.font_list if not f[-1] in "bi"]
            if normal_fonts:
                return os.path.join(
                    r"C:\Windows\Fonts", self.random_element(normal_fonts) + ".ttf"
                )
            return os.path.join(
                r"C:\Windows\Fonts", self.random_element(self.font_list) + ".ttf"
            )
        if mode and mode.lower() in "ib":
            foot_pool = []
            for font in self.font_list:
                if font.lower().endswith(mode.lower()):
                    foot_pool.append(font)

            if foot_pool:
                return os.path.join(
                    r"C:\Windows\Fonts", self.random_element(foot_pool) + ".ttf"
                )
        return os.path.join(
            r"C:\Windows\Fonts", self.random_element(self.font_list) + ".ttf"
        )

    def image(self, width=None, height=None):
        """
        返回各个语言的图片
        :param width: 宽
        :param height: 高
        :return: Image
        """
        path = self.random_element(self.image_list)
        img = Image.open(path)
        if not width or not height:
            return img
        return img.resize((width, height))

    def person(self):
        headers = {
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        response = requests.get(
            "https://thispersondoesnotexist.com/image", headers=headers
        )
        return Image.open(io.BytesIO(response.content))
