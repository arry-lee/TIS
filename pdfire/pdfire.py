"""
读取pdf文件保存成为模板
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


# PDFObjRef
import os
import random
import sys

from PIL import Image, ImageDraw
from pdfminer.converter import PDFConverter
from pdfminer.layout import LAParams, LTCurve, LTPage
from pdfminer.layout import LTChar, LTFigure, LTImage, LTLine, LTTextLine
from pdfminer.layout import LTTextBox, LTTextGroup
from pdfminer.pdfinterp import (
    PDFPageInterpreter,
    PDFResourceManager,
    PDFTextExtractionNotAllowed,
)
from pdfminer.pdfparser import PDFDocument, PDFParser
from tqdm import tqdm

from template import Template, Text


class JPGConverter(PDFConverter):
    """将pdf文件转换为jpg"""
    RECT_COLORS = {
        "char"     : "green",
        "figure"   : "black",
        "textline" : "black",
        "textbox"  : "green",
        "textgroup": "red",
        "curve"    : "black",
        "page"     : "black",
    }
    
    TEXT_COLORS = {
        "textbox": "red",
        "char"   : "black",
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
    ):
        PDFConverter.__init__(self, rsrcmgr, outfp, pageno=pageno,
                              laparams=laparams)
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
        self.draw = None
        self.pg_h = 0
        self.fn = os.path.splitext(os.path.split(fn)[1])[0]
        self.outfp = open(
            os.path.join(self.outdir, "train.txt"), "wt", encoding="utf-8"
        )
        self._line_no = ""
        self._lno = 0
        
        self.textbox_list = []
    
    def place_rect(self, color, borderwidth, x, y, w, h, rbg=None):
        color = self.rect_colors.get(color)
        
        if color is not None:
            rect = [
                x * self.scale,
                (self.pg_h - y + 1) * self.scale,
                (x + w) * self.scale,
                (self.pg_h - y + h - 1) * self.scale,
            ]
            
            self.draw.rectangle(rect, outline=color, width=borderwidth,
                                fill=rbg)
    
    def place_border(self, color, borderwidth, item, rbg=None):
        if isinstance(item, LTTextLine):
            rect = [
                item.x0 * self.scale,
                (self.pg_h - item.y1 + 1) * self.scale,
                (item.x0 + item.width) * self.scale,
                (self.pg_h - item.y1 + item.height - 1) * self.scale,
            ]
            self.textbox_list.append(Text(box=rect))
        else:
            self.place_rect(
                color, borderwidth, item.x0, item.y1, item.width, item.height,
                rbg
            )
    
    def place_image(self, item, borderwidth, x, y, w, h):
        # if self.outdir is not None:
        # name = self.write_image(item)
        # img = Image.open(name).resize((w * self.scale, h * self.scale))
        # self.draw.bitmap((x * self.scale, (self.pg_h-y) * self.scale),img)
        rbg = random.randint(0, 255), random.randint(0, 255), random.randint(0,
                                                                             255)
        self.place_border("red", borderwidth, item, rbg)
    
    def place_text(self, color, text, x, y, size, fontname=None,
                   showrect=False):
        color = self.text_colors.get(color)
        # print(text)
        if color is not None:
            fontsize = int(size * self.scale * self.fontscale)
            # if fontname:
            #     if isinstance(fontname, PDFTrueTypeFont):
            #         font = ImageFont.truetype(
            #             io.BytesIO(fontname.fontfile.get_data()), fontsize)
            #     elif isinstance(fontname, PDFCIDFont):
            #         font = ImageFont.truetype(self.default_font, fontsize)
            #         # cid = fontname.cmap.chardisp(1)
            #         # print(cid)
            #         # print(fontname.to_unichr(cid))
            #
            #     try:
            #         print(fontname)
            #         font = ImageFont.truetype(
            #             io.BytesIO(fontname.fontfile.get_data()), fontsize)
            #     except Exception as e:
            #         # print(e,fontname)
            #         try:
            #             font = ImageFont.truetype(fontname.basefont, fontsize)
            #         except Exception as ee:
            #             print(ee)
            #             font = ImageFont.truetype(self.default_font, fontsize)
            # else:
        # font = ImageFont.truetype(self.default_font, 10)
        # self.draw.text((x * self.scale, (self.pg_h - y) * self.scale), text,
        #                    fill='black', font=font)
        #
        #     if showrect:
        #         box = self.draw.textbbox(
        #             (x * self.scale, (self.pg_h - y) * self.scale),
        #             text.rstrip(), font=font)
        #         box0 = self.draw.textbbox((box[2], box[1]), text.strip(),
        #                                   font=font, anchor='rt')
        #         self.draw.rectangle(box0, outline='green', width=1)
    
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
                w, h = round(item.width * self.scale), round(
                    item.height * self.scale)
                self.pg_h = item.height
                self.image = Image.new("RGB", (w, h), "white")
                self.draw = ImageDraw.Draw(self.image)
                
                for child in item:
                    render(child)
                #
                # self.textbox_list = group(self.textbox_list)
                # for box in self.textbox_list:
                #     # b.check_direction()
                #     # b.shrink()
                #     self.draw.rectangle(
                #         [box.left, box.top, box.right, box.bottom],
                #         outline=(0, 255, 0, 100),
                #         width=2,
                #     )
                self.image.save(
                    os.path.join(self.outdir, "page%d.jpg" % item.pageid))
                tpl = Template(self.image, self.textbox_list)
                tpl.save(os.path.join(self.outdir, "page%d.tpl" % item.pageid))
                self.textbox_list.clear()
            
            
            elif isinstance(item, LTCurve):
                self.place_border('curve', 0, item, rbg=(0, 0, 0))
            
            elif isinstance(item, LTLine):
                self.place_border('curve', 0, item, rbg=(0, 0, 0))
            
            elif isinstance(item, LTFigure):
                self.place_border('figure', 2, item, rbg=(0, 0, 200))
                for child in item:
                    render(child)
            
            elif isinstance(item, LTImage):
                self.place_border('figure', 2, item, rbg=(0, 0, 200))
                pass
            
            else:
                if isinstance(item, LTTextBox):
                    for child in item:
                        render(child)
                elif isinstance(item, LTTextLine):
                    if item.width > item.height:
                        self.place_border('figure', 2, item, rbg=(200, 200, 0))
                
                elif isinstance(item, LTChar):
                    pass
                    # text = item.get_text()
                    # x1, y1, x2, y2 = (
                    #     int(item.x0 * self.scale),
                    #     int((self.pg_h - item.y1) * self.scale),
                    #     int(item.x1 * self.scale),
                    #     int((self.pg_h - item.y0) * self.scale),
                    # )
                    # if text.strip():
                    #     self.textbox_list.append(TextBox(x1, y1, x2, y2, text))
        
        render(ltpage)
    
    def close(self):
        self.outfp.close()


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
    # Create a PDF parser object associated with the file object.
    parser = PDFParser(fp)
    # Create a PDF document object that stores the document structure.
    doc = PDFDocument(caching=caching)
    # Connect the parser and document objects.
    parser.set_document(doc)
    doc.set_parser(parser)
    # Supply the document password for initialization.
    # (If no password is set, give an empty string.)
    doc.initialize(password)
    # Check if the document allows text extraction. If not, abort.
    if check_extractable and not doc.is_extractable:
        raise PDFTextExtractionNotAllowed(
            "Text extraction is not allowed: %r" % fp)
    # Create a PDF interpreter object.
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    # Process each page contained in the document.
    
    pbar = tqdm(total=len([f for f in doc.get_pages()]))
    for (pageno, page) in enumerate(doc.get_pages()):
        if pagenos and (pageno not in pagenos):
            continue
        interpreter.process_page(page)
        if maxpages and maxpages <= pageno + 1:
            break
        pbar.update(1)
    pbar.close()


if __name__ == "__main__":
    import glob
    
    outdir = r"E:\00IT\P\uniform\static\pdf"
    rsrcmgr = PDFResourceManager(caching=False)
    outfp = sys.stdout
    files = [f for f in glob.glob(os.path.join(outdir, "*.pdf"))]
    
    pdffile = r"test.pdf"
    laparams = LAParams()
    # scale = 2339/4210*5*2
    device = JPGConverter(
        rsrcmgr,
        outfp,
        outdir=outdir,
        fn=pdffile,
        scale=2,
        showpageno=False,
        laparams=laparams,
    )
    process_pdf(rsrcmgr, device, open(pdffile, "rb"), maxpages=5)
    device.close()
