"""生成二维码和条形码图像"""
import barcode
from PIL import Image
from barcode.writer import ImageWriter
from qrcode import QRCode


def qrcode_image(data):
    """二维码图像"""
    qrc = QRCode()
    qrc.add_data(str(data))
    return qrc.make_image()


def barcode_image(num="123456789100"):
    """条形码图像"""
    brc = barcode.get("ean13", str(num), writer=ImageWriter())
    return Image.open(brc.save("tmp")).crop((10, 0, 500, 200))
