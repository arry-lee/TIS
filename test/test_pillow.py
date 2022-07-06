from PIL import Image
from PIL.ImageOps import invert, solarize, expand
import pipes

# with Image.open("sqr.png") as im:
#     im.rotate(15,expand=True).show()
# 创建渐变
im = Image.linear_gradient("L").resize((500, 1000))

# expand(solarize(invert(Image.radial_gradient('L').resize((500,1000)))),20).show()
from PIL.ImageGrab import grab

# grab().show()
