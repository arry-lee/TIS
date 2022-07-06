from PyQt5.QtCore import QFile, QIODevice, QMarginsF, QSizeF, Qt
from PyQt5.QtGui import QFont, QPainter, QPdfWriter, QPen
from PyQt5.QtWidgets import QApplication, QWidget

# 1 pix = 1 mm
# dpi = 1pix/mm = 25.4 pix/inch

DPM = 10  # 1MM 10像素
DPI = 10 * 25.4
MM = 1 / DPM


# PT = 1200 / 72
# IN = PT * 72
# MM = 25.4 / 72

# location,label,color,font,size


class PdfWriter(QWidget):
    def __init__(self, *arg):
        super(PdfWriter, self).__init__(*arg)

    def render_pdf(self, data, outfile):
        image = data["image"]
        labels = data["label"]
        boxes = data["boxes"]
        h, w = image.shape[:2]
        print(h, w)
        pdfFile = QFile(outfile)
        pdfFile.open(QIODevice.WriteOnly)
        pw = QPdfWriter(pdfFile)
        pw.setPageSizeMM(QSizeF(w * MM, h * MM))
        pw.setResolution(DPI)
        pw.setPageMargins(QMarginsF(0, 0, 0, 0))
        painter = QPainter(pw)
        _font = QFont()
        _font.setFamily("simfang.ttf")
        _font.setPixelSize(20)
        painter.setFont(_font)
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))

        for label, box in zip(labels, boxes):
            print(label, box)
            if label == "cell@":
                painter.drawLine(box[0], box[1], box[0], box[3])
                painter.drawLine(box[2], box[1], box[2], box[3])
                painter.drawLine(box[0], box[1], box[2], box[1])
                painter.drawLine(box[0], box[3], box[2], box[3])
            elif label == "table@0":
                continue
            else:
                painter.drawText(box[0], box[3], label[5:])

        painter.end()
        pdfFile.close()


def render_pdf(data, outfile):
    import sys

    app = QApplication(sys.argv)
    pWrite = PdfWriter()
    pWrite.render_pdf(data, outfile)
    pWrite.close()
    app.quit()


if __name__ == "__main__":
    from image import table2image
    from converter import from_list

    test = [
        "项目",
        ["本年金额", [["gv", [2, 3, 4, [2, [3, 4]], 6, 7]], "少数", "所有者"]],
    ]

    tab = from_list(test, False)
    data = table2image(tab)
    render_pdf(data, "1.pdf")
