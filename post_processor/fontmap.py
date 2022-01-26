# 对第一步生成的表格增加格式
from PIL import ImageFont,Image,ImageDraw
import re
from post_processor.deco import c2p,p2c
from post_processor.seal import gen_name_seal, gen_seal, add_seal

FONTMAP = {'仿宋':'simfang.ttf',
           '黑体':'simhei.ttf',
           '楷体':'simkai.ttf'}


def apply_seals(data):
    boxes = data['boxes']  # box 和 label是一一对应的
    labels = data['label']
    image = c2p(data['image'])
    draw = ImageDraw.Draw(image)
    for idx,(box,label) in enumerate(zip(boxes,labels)):
        if label.lstrip('text@').startswith('编制单位'):
            company = label.lstrip('text@编制单位:')
            xy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
            print(xy)
            company_seal = gen_seal(company, bottom_text='财务专用章', center_text='2022.01.01', width=200)
            image = add_seal(image,company_seal,xy)

        elif label.lstrip('text@').endswith('〇'):
            name = label.lstrip('text@').rstrip('〇')
            name_seal = gen_name_seal(name,40,True)

            xy = (box[0] + box[2]) // 2 - 20, (box[1] + box[3]) // 2-20
            print(name,xy)
            image = add_seal(image, name_seal,xy)
    data['image'] = p2c(image)
    return data

def apply_font_map(data,font_map,basesize):
    """将满足某个正则表达式的字符映射到对应的字体上"""
    boxes = data['boxes']  # box 和 label是一一对应的
    labels = data['label']
    image = c2p(data['image'])
    draw = ImageDraw.Draw(image)
    for idx,(box,label) in enumerate(zip(boxes,labels)):
        if not label.startswith('text'):
            continue
        size = box[3]-box[1]
        text = label.split('@')[-1]
        for pat,font_tuple in font_map:
            if re.match(pat,text):
                fp,font_size,stroke_width = font_tuple
                font = ImageFont.truetype(fp,font_size)
                if font_size > basesize: # 放大字体居中对齐
                    xy = (box[0]+box[2])//2,(box[1]+box[3])//2
                    anchor = 'mm'
                elif font_size < basesize: # 缩小字体左中对齐
                    xy = box[0],(box[1]+box[3])//2
                    anchor = 'lm'
                else:
                    xy =  box[0],box[1] # 不变左上对齐
                    anchor = 'lt'
                draw.rectangle(box,fill='white')
                draw.text(xy,text,fill='black',font=font,anchor=anchor,stroke_width=stroke_width,stroke_fill='black')
                data['boxes'][idx] = draw.textbbox(xy,text,font=font,anchor=anchor)
                break
    data['image'] = p2c(image)
    return data



def apply_cell_map(data,cell_map):
    """ 对于某个满足条件func 的 box,对其图像执行 handler
    cell_map = [(lambda box:True,lambda img:img.filp())]
    """
    boxes = data['boxes']  # box 和 label是一一对应的
    labels = data['label']
    image = c2p(data['image'])
    draw = ImageDraw.Draw(image)
    for idx,(box,label) in enumerate(zip(boxes,labels)):
        if not label.startswith('cell'):
            continue
        for func,handler in cell_map:
            if func(box):
                image.paste(handler(image.crop(box)),box)
                break
    data['image'] = p2c(image)
    return data