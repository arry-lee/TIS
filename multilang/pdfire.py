"""
读取pdf文件保存成为模板

问题：
1. 有的字体没有内嵌的字体文件
2. 有的字体没有办法正常显示

"""
# pdfire 的哲学是 python 足够强大可以解析 pdf； 目标是把 pdf 渲染成 png 格式的图片
# 包括字体颜色和比例，都能1比1还原。

# 思路

# pdfparser 解析器
# pdfinterp 解释器
# pdfdevice 输出设备

# 对于每个字符，它的外接矩形是精确的，

# 视为字符串的
# 横向：self.right == other.left and self.top == other.top and self.bottom == other.bottom
# 纵向：self.bottom == other.top and self.left == other.left and self.right == other.right

# group分组：按top分组，在每一个分组里按left排序，创建空栈 stack ，将该组的成员压栈，入栈条件是 self.right == other.left。
# 无法入栈时将内部元素重组；
# 剩余元素按照left分组，按top排序
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pdfminer.converter import PDFConverter
from pdfminer.image import ImageWriter
from pdfminer.layout import LAParams, LTCurve, LTPage, LTRect, LTTextLine
from pdfminer.layout import LTChar, LTFigure, LTImage, LTLine
from pdfminer.layout import LTTextBox, LTTextGroup
from pdfminer.pdfinterp import (
    PDFPageInterpreter,
    PDFResourceManager,
)
from pdfminer.pdfpage import PDFPage
from pdfminer.pdftypes import stream_value
from pyrect import Rect
from tqdm import tqdm

from postprocessor.convert import p2c
from multilang.template import Template, Text

from paddleocr import PaddleOCR
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
OCR_ENGINE = None#PaddleOCR(lang="ch",show_log=False)

def ocr(image, ocr_engine=None):
    """
    从图片识别模板
    :param image: 图像文件名
    :param ocr_engine: OCR 引擎，若未设置会尝试导入 PaddleOcr
    :return: Template 实例
    """
    if ocr_engine is None:
        ocr_engine = OCR_ENGINE
    if isinstance(image,Image.Image):
        image = p2c(image)[:,:,3]
        
    results = ocr_engine.ocr(image,cls=False)
    texts = []
    for box, content in results:
        text, _ = content
        texts.append(
            Text(
                text=text,
                rect=Rect(
                    box[0][0],
                    box[0][1],
                    box[2][0] - box[0][0],
                    box[2][1] - box[0][1],
                ),
            )
        )

    return texts


def remove_duplicate(text):
    """
    最小循环子串
    """
    index = (text + text).find(text, 1)
    if index > 0:
        return text[:index]
    return text


class ImageExporter(ImageWriter):
    def _create_unique_image_name(self, image: LTImage, ext: str):
        name = image.name + ext
        path = os.path.join(self.outdir, name)
        return name, path

    def export_image(self, image: LTImage):
        """重写方法以实现导出RGBA格式的PNG图片"""
        name = super().export_image(image)
        path = os.path.join(self.outdir, name)
        img = Image.open(path)
        
        if name.endswith("bmp"):  # 原来的 ImageWriter产生bmp 是bgr格式的有错误
            red, green, blue = img.split()
            img = Image.merge("RGB", (blue, green, red))
        img = img.convert("RGBA")
        if image.imagemask:
            stream = image.imagemask.resolve()
            mask = LTImage("M" + image.name, stream, image.bbox)
            mask_name = super().export_image(mask)
            mask_path = os.path.join(self.outdir, mask_name)
            mask_image = Image.open(mask_path)
            img.putalpha(mask_image)
            try:
                os.remove(mask_path)
            except PermissionError:
                pass
        try:
            os.remove(path)
        except PermissionError:
            pass

        return img


class TemplateConverter(PDFConverter):
    """将pdf文件转换为jpg"""

    RECT_COLORS = {
        "char": "green",
        "figure": "black",
        "textline": "black",
        "textbox": "green",
        "textgroup": "red",
        "curve": (200, 0, 0),
        "page": "black",
    }

    TEXT_COLORS = {
        "textbox": "red",
        "char": "black",
    }

    def __init__(
        self,
        rsrcmgr,
        outfp,
        fn="",
        pageno=1,
        laparams=None,
        scale=1,
        fontscale=1,
        layoutmode="normal",
        showpageno=True,
        pagemargin=50,
        outdir=None,
        rect_colors={"curve": "black", "page": "gray"},
        text_colors={"char": "black"},
        use_ocr=False
    ):
        PDFConverter.__init__(self, rsrcmgr, outfp, pageno=pageno, laparams=laparams)

        
        self.scale = scale
        self.fontscale = fontscale
        self.layoutmode = layoutmode
        self.showpageno = showpageno
        self.pagemargin = pagemargin
        self.outdir = outdir or "."  # 输出文件夹
        if not os.path.exists(self.outdir):
            os.mkdir(self.outdir)
        self.rect_colors = rect_colors
        self.text_colors = text_colors
        self.rect_colors.update(self.RECT_COLORS)
        self.text_colors.update(self.TEXT_COLORS)

        self._yoffset = self.pagemargin
        self._font = None
        self._fontstack = []

        self.default_font = "arial.ttf"
        self.images = []

        self.page_height = 0
        self.fn = os.path.splitext(os.path.split(fn)[1])[0]
        self.outfp = open(
            os.path.join(self.outdir, "train.txt"), "wt", encoding="utf-8"
        )
        self._line_no = ""
        self._lno = 0

        self.textbox_list = []
        self.figure_list = []
        
        self.imagewriter = ImageExporter(self.outdir)
        self.template_list = []
        self.text_layer = None
        self.pen = None
        self.image = None
        self.draw = None
        self.use_ocr = use_ocr
        
    def place_rect(self, color, borderwidth, x, y, w, h, rbg=None):
        if color is not None:
            rect = [
                x * self.scale,
                (self.page_height - y + 1) * self.scale,
                (x + w) * self.scale,
                (self.page_height - y + h - 1) * self.scale,
            ]

            self.draw.rectangle(rect, outline=color, width=borderwidth, fill=rbg)

    def place_border(self, color, borderwidth, item, rbg=None, font=None):
        if isinstance(item, LTTextLine):
            self.textbox_list.append(
                Text(
                    text=item.get_text(),#remove_duplicate(item.get_text().strip()),
                    rect=Rect(
                        item.x0 * self.scale,
                        (self.page_height - item.y1) * self.scale,
                        item.width * self.scale,
                        item.height * self.scale,
                    ),
                    color=rbg,
                    font=font,
                )
            )
        elif isinstance(item, (LTLine,LTRect)):
            self.place_rect(
                color, borderwidth, item.x0, item.y1, item.width, item.height, None
            )

    def place_image(self, item):
        width = int(item.width * self.scale)
        height = int(item.height * self.scale)
        ptx = int(item.x0 * self.scale)
        pty = int((self.page_height - item.y1) * self.scale)

        img = self.imagewriter.export_image(item)
       
        
        if width > 0 and height > 0:
            img = img.resize((width, height))
        
        
        def is_watermark(img):
            """简单的判断是否为水印"""
            return False
        
        def is_opacity(img):
            return np.any(np.asarray(img.getchannel('A'),np.uint8)==0)

        if not is_watermark(img):
            # 处理有透明层的文字
            if self.use_ocr and is_opacity(img):
                texts = ocr(img)
                print(texts)
                if len(texts)>0:
                    for text in texts:
                        text.rect.move(ptx, pty)
                        self.textbox_list.append(text)
                else:
                    self.image.paste(img, (ptx, pty), mask=img)
            else:
                self.image.paste(img, (ptx, pty), mask=img)
                # self.image.save(os.path.join(self.outdir,'/element/{}'))
                self.textbox_list.append(
                    Text(
                        text='<LTImage>',
                        rect=Rect(
                            ptx,
                            pty,
                            width,
                            height
                        ),
                    )
                )
        else:
            print(img.getcolors())

    def place_text(self, color, text, x, y, size, fontname=None, showrect=False):
        color = self.text_colors.get(color)
        if color is not None:
            fontsize = int(size * self.scale * self.fontscale)

    def receive_layout(self, ltpage):
        """处理单页"""

        def show_group(item):
            if isinstance(item, LTTextGroup):
                self.place_border("textgroup", 10, item)
                for child in item:
                    show_group(child)

        def render(item):
            if isinstance(item, LTPage):
                # 如果是一页，创建一个新的图片
                init_page(item)
                for child in item:
                    render(child)
                save_page(item)

            elif isinstance(item, LTCurve):
                self.place_border(
                    covert_color(item.stroking_color),
                    1 + int(item.linewidth * self.scale),
                    item,
                    covert_color(item.non_stroking_color),
                )

            elif isinstance(item, LTLine):
                self.place_border(
                    covert_color(item.stroking_color),
                    1 + int(item.linewidth * self.scale),
                    item,
                    covert_color(item.non_stroking_color),
                )

            elif isinstance(item, LTRect):
                self.place_border(
                    covert_color(item.stroking_color),
                    1 + int(item.linewidth * self.scale),
                    item,
                    covert_color(item.non_stroking_color),
                )

            elif isinstance(item, LTFigure):
                for child in item:
                    render(child)

            elif isinstance(item, LTImage):
                self.place_image(item)
                # pass
            else:
                if isinstance(item, LTTextBox):
                    for child in item:
                        render(child)
                elif isinstance(item, LTTextLine):
                    color = None
                    font = None
                    for child in item:
                        if not color:
                            color = covert_color(child.graphicstate.ncolor)
                        if not font and isinstance(child, LTChar):
                            font = "b" if "bold" in child.fontname.lower() else None
                        render(child)
                    if item.width > item.height:
                        self.place_border(color, 2, item, rbg=color, font=font)

                elif isinstance(item, LTChar):
                    # 单独分一个文字层出来？
                    x = int(item.x0 * self.scale)
                    y = int((self.page_height - item.y1) * self.scale)
                    # text = item.get_text()
                    # print(item.graphicstate)
                    color = covert_color(item.graphicstate.ncolor)
                    color = (*color, 255)
                    
                    # print(stream_value(font))
                    fontfile = item.font.descriptor.get("FontFile2")
                    # print(item.font.descriptor)

                    if fontfile:
                        stream = stream_value(fontfile)#.resolve()
                        data = stream.get_data() #fix
                        # print(stream.attrs)
                        # font = self.rsrcmgr.get_font(stream.objid,
                        #                              item.font.descriptor)
                        # print(font.descriptor)
                        # print(item.font.descriptor.get('FontName'))
                        ftsize = int(item.height * self.scale)
                        # print(ftsize)
                        _font = ImageFont.truetype(
                            io.BytesIO(data), int(item.height * self.scale),
                        )
                        # print(_font.path,_font.getname())
                        self.pen.text(
                            (x, y),
                            item.get_text(),
                            color,
                            _font,
                        )
                    # else:
                    #     print('No font')
                        # self.pen.text(
                        #     (x, y),
                        #     item.get_text(),
                        #     color,
                        #     _font,
                        # )
                        # _font = ImageFont.truetype('simfang.ttf',int(item.height * self.scale))
                    
                    # if item.get_text().isdigit():
                    #     print(repr(item))
                    # else:
                    #     print(repr(item)+'@')
                    # if item.adv < 1:
                    #     print(repr(item),int(item.height * self.scale))
                    #     x = int(item.x0 * self.scale)
                    #     y = int((self.page_height - item.y1-item.height) * self.scale)
                    # else:
                    
                    # todo: #issue006, PDF 转换过程中数字框的位置不对
                    # print(item.get_text())
                    

        def init_page(page):
            """ 初始化页面 """
            page_size = round(page.width * self.scale), round(page.height * self.scale)
            self.page_height = page.height
            self.image = Image.new("RGB", page_size, "white")
            self.draw = ImageDraw.Draw(self.image)
            self.text_layer = Image.new("RGBA", page_size, (0, 0, 0, 0))
            self.pen = ImageDraw.Draw(self.text_layer)

        def save_page(item):
            """ 保存页面 """
            self.image.save(os.path.join(self.outdir, f"{self.fn}-{item.pageid}.jpg"))
            self.text_layer.save(
                os.path.join(self.outdir, f"{self.fn}-{item.pageid}.png")
            )
            tpl = Template(self.image, self.textbox_list)
            tpl_name = os.path.join(self.outdir, f"{self.fn}-{item.pageid}.tpl")
            tpl.save(tpl_name)
            self.template_list.append(tpl_name)
            self.textbox_list.clear()
            self.image.paste(self.text_layer, mask=self.text_layer)
            self.image.save(os.path.join(self.outdir, f"{self.fn}-{item.pageid}-a.png"))

        render(ltpage)

    def close(self):
        self.outfp.close()


def cmyk_to_rgb(cmyk):
    return (
        255 * (1.0 - (cmyk[0] + cmyk[3])),
        255 * (1.0 - (cmyk[1] + cmyk[3])),
        255 * (1.0 - (cmyk[2] + cmyk[3])),
    )


def covert_color(color):
    if isinstance(color, float):
        # print('color error',color)
        c = int(color*255)
        return (c,c,c)
    if isinstance(color,int):
        return color,color,color
    
    if color is None:
        return (0, 0, 0)
    if len(color) == 1:
        if isinstance(color[0],(int,float)):
            return color[0] * 255, color[0] * 255, color[0] * 255
        else:
            return 0,0,0
    if len(color) == 4:
        color = cmyk_to_rgb(color)
    if len(color) == 3:
        return int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
    raise ValueError("Color Error")


def process_pdf(
    rsrcmgr,
    device,
    fp,
    pagenos=None,
    maxpages=0,
    password="",
    caching=True,
    check_extractable=True,
):
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    pages = PDFPage.get_pages(
        fp, pagenos, maxpages, password, caching, check_extractable
    )

    for page in pages:
        try:
            interpreter.process_page(page)
        except Exception as e:
            raise (e)


def from_pdf(file, outdir=None, maxpages=0, use_ocr=False):
    """
    PDF 文件转换为 模板文件
    :param maxpages: 最大页数，为0则全部
    :param file: pdf文件
    :param outdir: 输出目录
    :return: 模板文件列表
    """
    if not outdir:
        outdir = os.path.dirname(os.path.abspath(file))
    rsrcmgr = PDFResourceManager(caching=True)
    device = TemplateConverter(
        rsrcmgr,
        sys.stdout,
        outdir=outdir,
        fn=file,
        scale=2, # defualt 2
        showpageno=False,
        laparams=LAParams(),
        use_ocr=use_ocr
    )
    process_pdf(rsrcmgr, device, open(file, "rb"), maxpages=maxpages)
    device.close()
    return device.template_list


if __name__ == "__main__":
    # print(from_pdf(r"E:\00IT\P\uniform\multilang\templates\menu\bn\0a9e2cfc53ad3fd0f7fc7fc97ef5f285.pdf"))
    im = Image.open(r'E:\00IT\P\uniform\multilang\templates\menu\filter\0e98196931ebaa85c5c734a3cb94dffa-2.png')
    t = ocr(im)
    print(t)