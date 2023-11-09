import glob
import os

from tqdm import tqdm

from multilang.pdfire import from_pdf


def iglob(path, ext):
    """
    生成目录 path 下后缀为ext的文件绝对路径
    :param path:
    :param ext:
    :return:
    """
    for i in glob.iglob(os.path.join(path, "*" + ext)):
        yield os.path.abspath(i)


def filter_templates(tpl_dir, filter_dir):
    """
    人工删除不好的效果图后，删去对应的模板
    :param tpl_dir: 模板目录
    :param filter_dir: 人工筛选剩余图片
    :return: 剩下的数量
    """
    filters = set()
    for fname in iglob(filter_dir, "g"):
        filters.add(os.path.splitext(os.path.basename(fname))[0])

    for tpl in iglob(tpl_dir, "tpl"):
        name = os.path.basename(tpl).removesuffix(".tpl")
        if name not in filters:
            os.remove(tpl)
            print(f"remove {tpl}")
    return len(filters)


def filter_pdfs(pdf_dir, filter_dir):
    """
    人工删除不好的效果图后，删去对应的PDF模板
    :param pdf_dir: pdf 目录
    :param filter_dir: 人工筛选剩余图片
    :return: 剩下的数量
    """
    filters = set()
    for fname in iglob(filter_dir, ".png"):
        filters.add(os.path.basename(fname).split("-")[0])

    for tpl in iglob(pdf_dir, "pdf"):
        name = os.path.basename(tpl).removesuffix(".pdf")
        if name not in filters:
            os.remove(tpl)
            print(f"remove {tpl}")
    return len(filters)


def prepare_templates(pdf_dir, tpl_dir, use_ocr=False):
    """
    准备模板文件夹
    :param pdf_dir: PDF 文件夹
    :param tpl_dir: 模板 文件夹
    :param use_ocr: 是否对PDF中的图片使用OCR识别,False 不识别
    :return: None
    """
    for file in tqdm(iglob(pdf_dir, ".pdf")):
        try:
            from_pdf(file, outdir=tpl_dir, maxpages=0, use_ocr=use_ocr)
        # pylint:disable=broad-except
        except (FileNotFoundError, Exception) as err:
            print(err)