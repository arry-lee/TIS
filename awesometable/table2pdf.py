import os

from PyQt5.QtCore import QFile, QIODevice, QMarginsF, QSizeF, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPdfWriter, QPen
from PyQt5.QtWidgets import QApplication, QWidget

# 1 pix = 1 mm
# dpi = 1pix/mm = 25.4 pix/inch

DPM = 10  # 1MM 10像素
DPI = 10 * 25.4
MM = 1 / DPM


def get_font(font):
    """ 将 ImageFont 转化为QtFont"""
    ft = QFont()
    ft.setFamily(os.path.split(font.path)[1].removesuffix('.ttf'))
    ft.setPixelSize(font.size)
    return ft


def get_color(c):
    color = QColor()
    if isinstance(c, tuple):
        color.setRgb(*c)
    elif isinstance(c, str):
        color.setNamedColor(c)
    else:
        raise KeyError('No such color')
    return color


class PdfWriter(QWidget):
    def __init__(self, *arg):
        super(PdfWriter, self).__init__(*arg)

    def render_pdf(self, data, outfile):
        image = data["image"]
        # labels = data["label"]
        # boxes = data["boxes"]
        text_list = data["text"]
        line_list = data["line"]
        h, w = image.shape[:2]

        pdfFile = QFile(outfile)
        pdfFile.open(QIODevice.WriteOnly)
        pw = QPdfWriter(pdfFile)
        pw.setPageSizeMM(QSizeF(w * MM, h * MM))
        pw.setResolution(DPI)
        pw.setPageMargins(QMarginsF(0, 0, 0, 0))
        painter = QPainter(pw)
        _font = QFont()
        _font.setFamily("Arial")
        _font.setPixelSize(40)
        painter.setFont(_font)
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))

        for t in text_list:
            _font.setPixelSize(t.font.size)
            painter.setFont(_font)
            painter.setPen(get_color(t.color))
            painter.drawText(t.box[0], t.box[3], t.text)

        for l in line_list:
            painter.setPen(QPen(Qt.black, l.width, Qt.SolidLine))
            painter.drawLine(l.start[0], l.start[1], l.end[0], l.end[1])

        painter.end()
        pdfFile.close()


def render_pdf(data, outfile):
    import sys
    app = QApplication(sys.argv)
    pWrite = PdfWriter()
    pWrite.render_pdf(data, outfile)
    pWrite.close()
    app.quit()
