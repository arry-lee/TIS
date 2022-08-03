"""
AwesomeTable 转 pdf 模块，使用了pyqt的 QPdfWriter
"""
import os
import sys

from PyQt5.QtCore import QFile, QIODevice, QMarginsF, QSizeF, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPdfWriter, QPen
from PyQt5.QtWidgets import QApplication, QWidget

# 1 pix = 1 mm
# dpi = 1pix/mm = 25.4 pix/inch

DPM = 10  # 1MM 10像素
DPI = 10 * 25.4
MM = 1 / DPM


def get_font(font):
    """将 ImageFont 转化为QtFont"""
    fnt = QFont()
    name = os.path.split(font.path)[1].removesuffix(".ttf")
    if name.startswith("a"):
        fnt.setFamily("Arial")
    elif name.startswith("sim"):
        fnt.setFamily("仿宋")
    fnt.setPixelSize(font.size)
    return fnt


def get_color(color):
    """将 pil color 转化为 qt color"""
    clr = QColor()
    if isinstance(color, tuple):
        clr.setRgb(*color)
    elif isinstance(color, str):
        clr.setNamedColor(color)
    else:
        raise KeyError("No such color")
    return clr


class PdfWriter(QWidget):
    """
    写入 pdf
    """

    def __init__(self, *arg):
        super().__init__(*arg)

    def render_pdf(self, data, outfile):
        """
        渲染 pdf
        :param data: 数据字典
        :param outfile: 输出文件名
        :return: None
        """
        image = data["image"]
        text_list = data["text"]
        line_list = data["line"]
        height, width = image.shape[:2]

        pdf_file = QFile(outfile)
        pdf_file.open(QIODevice.WriteOnly)
        pdf_writer = QPdfWriter(pdf_file)
        pdf_writer.setPageSizeMM(QSizeF(width * MM, height * MM))
        pdf_writer.setResolution(DPI)
        pdf_writer.setPageMargins(QMarginsF(0, 0, 0, 0))
        painter = QPainter(pdf_writer)
        _font = QFont()
        _font.setFamily("Arial")
        _font.setPixelSize(40)
        painter.setFont(_font)
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))

        for text in text_list:
            painter.setFont(get_font(text.font))
            painter.setPen(get_color(text.color))
            painter.drawText(text.box[0], text.box[3], text.text)

        for line in line_list:
            painter.setPen(QPen(Qt.black, line.width, Qt.SolidLine))
            painter.drawLine(line.start[0], line.start[1], line.end[0], line.end[1])

        painter.end()
        pdf_file.close()


def render_pdf(data, outfile):
    """
    渲染 pdf
    :param data: dict 字典数据
    :param outfile: 输出文件
    :return:
    """
    app = QApplication(sys.argv)
    writer = PdfWriter()
    writer.render_pdf(data, outfile)
    writer.close()
    app.quit()
