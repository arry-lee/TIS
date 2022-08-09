from dataclasses import dataclass
from typing import Any, Tuple

import pickle

from PIL import ImageDraw


class Template:
    ext = 'tpl'
    
    def __init__(self, image, texts):
        self.image = image
        self.texts = texts
    
    def render(self, backend='jpg'):
        """
        渲染模板成图片
        :param backend: 后端可以是 JPG 和 PDF
        :return:
        """
        image = self.image.copy()
        draw = ImageDraw.Draw(image)
        for text in self.texts:
            draw.rectangle(text.box, outline='green',width=2)
        return image
    
    def save(self, path):
        """将实例保存成模板文件"""
        with open(path, 'wb') as file:
            pickle.dump(self, file)
    
    def replace_texts(self, engine):
        """
        替换模板文本
        :param engine: 使用的引擎，可以是Faker，可以是Trans
        :return: None
        """
        for text in self.texts:
            text.text = engine.words()
            text.font = engine.font()
    
    def clean_texts(self):
        for text in self.texts:
            text.text = ''
    
    @staticmethod
    def load(path):
        """从模板文件加载模板实例"""
        with open(path, 'rb') as file:
            obj = pickle.load(file)
        return obj
    
    @classmethod
    def from_pdf(cls):
        """从pdf文件加载模板实例"""
        pass
    
    @classmethod
    def from_txt(cls):
        """从标注文件加载模板实例"""
        pass


@dataclass
class Text:
    """文本框"""
    pos: Tuple[int, int] = None
    text: str = ''
    font: Any = None
    anchor: str = "lt"
    color: Any = "black"
    box: Tuple[int, int, int, int] = None


if __name__ == '__main__':
    t = Template.load(r'E:\00IT\P\uniform\static\pdf\page1.tpl')
    im = t.render()
    im.show()
