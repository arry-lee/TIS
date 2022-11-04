"""
# __author__: arry_lee<arry_lee@qq.com>
# 解决英文多行文本的排版问题
"""

from PIL import Image, ImageDraw, ImageFont


def multiline(text, fill, font_path, fontsize, mode="-"):
    if mode == "-":
        return put_text_in_box(text, fill, font_path, fontsize, break_word=True)
    if mode == "":
        return put_text_in_box(text, fill, font_path, fontsize, break_word=False)
    if mode == " ":
        return put_text_in_box_without_break_word(text, fill, font_path, fontsize)


def put_text_in_box(
    text,
    width=None,
    fill="black",
    font_path="arial.ttf",
    font_size=20,
    line_pad=4,
    break_word=True,
    indent=0,
):
    """
    软换行但是不调整空格宽度
    :param text: 没有换行的完整英文句子
    :param width: 最大可用宽度 如果为None 则排成一行
    :param fill: 颜色
    :param font_path: 字体文件路径
    :param font_size: 字体大小
    :param line_pad: 行距
    :param break_word: 是否在单词中间打断并加上连字符'-'
    :param indent: 是否缩进
    :return: tuple[str,PIL.Image,list]
    """
    font = ImageFont.truetype(font_path, font_size)
    if not width:
        width = font.getsize(text)[0]
    img = Image.new("RGB", (width, width), "white")
    draw = ImageDraw.Draw(img)
    
    space_width = font.getsize(" ")[0]

    for i in text:
        if i.isspace():
            indent += 1
        else:
            break
    words = text.split()
    lines = []
    line = ""
    boxes = []
    x, y = space_width * indent, 0
    x0 = x
    for word in words:
        bbox = draw.textbbox((x, y), word, font)
        if bbox[2] < width:
            draw.text((x, y), word + " ", fill, font)
            line += word + " "
            x = bbox[2] + space_width
        elif bbox[2] > width:
            if break_word:
                for i, c in enumerate(word):
                    bbox = draw.textbbox((x, y), c, font)
                    if bbox[2] < width - space_width:
                        draw.text((x, y), c, fill, font)
                        line += c
                        x = bbox[2]
                    else:
                        if i > 0:
                            draw.text((x, y), "-", fill, font)
                            line += "-"
                        lines.append(line)
                        boxes.append((x0, y, width, y + font_size))
                        x = 0
                        x0 = 0
                        y += font_size + line_pad
                        line = word[i:] + " "
                        draw.text((x, y), line, fill, font)
                        x = draw.textbbox((x, y), line, font)[2]
                        break
            else:  # 放不下就换一行
                lines.append(line)
                boxes.append((x0, y, width, y + font_size))
                x = 0
                x0 = 0
                y += font_size + line_pad
                line = word + " "
                draw.text((x, y), line, fill, font)
                x = draw.textbbox((x, y), line, font)[2]
        else:
            draw.text((x, y), word, fill, font)
            line += word
            lines.append(line)
            boxes.append((x, y, width, y + font_size))
            line = ""
            x = 0
            y += font_size + line_pad

    lines.append(line)
    bbox = draw.textbbox((0, y), line, font)
    boxes.append(bbox)
    height = y + font_size + line_pad
    img = img.crop((0, 0, width, height))
    return "\n".join(lines), img, boxes


def put_text_in_box_without_break_word(
    text, width=None, indent=0, fill="black", font_path="arial.ttf", font_size=20, line_pad=5
):
    """
    软换行而且调整空格宽度来实现两端对齐
    :param text: str 没有换行的完整英文句子
    :param width: int 最大可用宽度
    :param indent: bool 是否缩进
    :param fill: tuple|str 颜色
    :param font_path: str|path 字体文件路径
    :param font_size: int 字体大小
    :param line_pad: int 行间距
    :return: tuple[str,PIL.Image,list]
    :algorithm:
    # 试图不打破单词进行换行，text 是个段落
    # 用栈存放单词，判断入栈条件，放不下的单词溢出的长度如果小等于栈中单词的数量，
    # 则可减少空格宽度并放入该词
    # 如果大于栈中单词数量则放弃，放入下一行
    """
    boxes = []
    lines = []
    line = []
    
    words = text.split()
    font = ImageFont.truetype(font_path, font_size)
    if not width:
        width = font.getsize(text)[0]
        
    space_width = font.getsize(" ")[0]
    max_space_diff = 0.1 * space_width  # 空格宽度变化百分比
    x0 = indent * space_width
    lens = x0
    for word in words:
        w = font.getsize(word)[0]
        if lens + w <= width:
            lens += w + space_width
            line.append(word)
        else:
            ex = lens + w - width  # 压缩量
            if ex <= len(line) * max_space_diff:
                line.append(word)
                line.append(-ex)
                lines.append(line)
                line = []
                lens = 0
            else:
                ex = width - lens + space_width  # 拉伸量
                line.append(ex)
                lines.append(line)
                line = [word]
                lens = w + space_width

    end_line = None
    if line and not isinstance(line[-1], int):
        end_line = " ".join(line)

    if end_line is None:
        height = len(lines) * (font_size + line_pad)
    else:
        height = (len(lines) + 1) * (font_size + line_pad)

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    x, y = x0, 0
    out = []
    for line in lines:
        start = x
        ex = line.pop()
        out.append(" ".join(line))
        sign = 1 if ex >= 0 else -1
        if len(line) > 1:
            n = abs(ex) // (len(line) - 1)
            m = abs(ex) % (len(line) - 1)
            sw = [space_width + n * sign] * (len(line) - 1)
            for i in range(m):
                sw[i] += sign
            sw.append(0)
        else:
            sw = [0]
        for w, word in zip(sw, line):
            draw.text((x, y), word, fill, font)
            x = draw.textbbox((x, y), word, font)[2] + w
        boxes.append((start, y, width, y + font_size))
        y += font_size + line_pad
        x = 0

    if end_line:
        draw.text((x, y), end_line, fill, font)
        boxes.append(draw.textbbox((x, y), end_line, font))
        out.append(end_line)
    return "\n".join(out), img, boxes


def draw_multiline_text(text, fill, font_path="arial.ttf", font_size=20):
    """
    通过像素偏移实现两端对齐
    :param text: str 已经换好行的英文文本
    :param fill: tuple|str 字体颜色
    :param font_path: str|path 字体文件路径
    :param font_size: int 字体大小
    :return: PIL.Image
    """
    text_list = text.splitlines()
    font = ImageFont.truetype(font_path, font_size)
    width = max(font.getsize(t)[0] for t in text_list) + font_size * 5
    img = Image.new("RGB", (width, font_size * len(text_list)), "white")
    draw = ImageDraw.Draw(img)
    x, y = 0, 0
    max_width = 0
    for t in text_list[:-1]:
        w = font.getsize(t)[0]
        pix = width - w
        chars = len(t) - 1
        n = pix // chars
        m = pix % chars
        offsets = [n] * chars
        for i in range(m):
            offsets[i] += 1
        offsets.append(0)

        for c, b in zip(t, offsets):
            draw.text((x, y), c, fill, font)
            w = font.getsize(c)[0]
            x += w + b
        max_width = max(max_width, x)
        x = 0
        y += font_size
    draw.text((x, y), text_list[-1], fill, font)
    height = y + font_size
    img = img.crop((0, 0, max_width, height))
    return img


def font_wrap(text, width, font_path="arial.ttf", font_size=40):
    """
    返回在某一字体字号下重新换行打包的字符串
    :param text: str 文本
    :param width: int 字符宽度
    :param font_path: str 字体路径
    :param font_size: int 字体尺寸
    :return: str
    """
    out, _, __ = put_text_in_box(
        text,
        width * font_size // 2,
        font_path=font_path,
        font_size=font_size,
        break_word=True,
        indent=0,
    )
    return out
