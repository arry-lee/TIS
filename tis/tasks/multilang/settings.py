"""
本文件存放项目中的所有常量和环境配置
"""
import os

"""
任务进度： 代码 对齐 调试 交付
身份证： - - -
报纸/杂志/书籍： - - -
优惠券：- -
菜单，名片，会员卡，银行卡，收银条，护照
表格，货运单，快递单：
"""

# 项目目录
BASE_DIR = os.path.split(os.path.abspath(__file__))[0]
# 模板目录
TEMPLATES_DIR = 'templates'
# 输出目录
OUTPUT_DIR = 'output_data'
# 任务模板字典
TEMPLATES_MAP = dict(身份证='idcard', 护照='passport', 银行卡='bankcard', 会员卡='vipcard',
                     名片='businesscard', 收银条='receipt', 快递单='express',
                     货运单='waybill', 优惠券='coupons', 书籍='book', 报纸='newspaper',
                     杂志='magazine', 表格='form', 菜单='menu', 包装='package')
# 模板类型，0:设计,1:pdf文件,2:图片文件,4:自动生成布局
TEMPLATE_TYPE = {
    0: 'DESIGN',
    1: 'PDF',
    2: 'IMAGE',
    4: 'LAYOUT'
}
# 多语言语料类型：0：翻译, 1:假数据, 2:爬虫
CORPUS_TYPE = {
    0: 'TRANSLATE',
    1: 'FAKER',
    2: 'SPIDER'
}
# 各个任务所采用的解决方案模板类型
SOLUTION_MAP = {
    0: ['名片', '优惠券', '菜单', '包装'],
    1: ['书籍', '报纸', '杂志'],
    2: ['身份证', '护照', '银行卡','会员卡'],
    4: ['快递单', '货运单', '表格']
}
# 多语言三元组(code,en,zh)
LANG_TUPLE = (
    ("id", "Indonesian", "印尼语"),
    ("fil_PH", "Filipino", "菲律宾语"),
    ("nl_be", "Dutch", "荷兰语"),
    ("cs", "Czech", "捷克语"),
    ("el_GR", "Greek", "希腊语"),
    ("bn", "Bengali", "孟加拉语"),
    ("ne", "Nepali", "尼泊尔语"),
    ("si", "Sinhala", "僧伽罗语"),
    ("km", "Khmer", "柬埔寨语"),
    ("lo_LA", "Lao", "老挝语"),
    ("ms_MY", "Malay", "马来语"),
)
# 多语言代码
LANG_CODES = [i[0] for i in LANG_TUPLE]


def build_dirs():
    """准备好所有的文件夹"""
    dirs = []
    for path in (TEMPLATES_DIR, OUTPUT_DIR):
        for task in TEMPLATES_MAP.values():
            for lang in LANG_CODES:
                dirs.append((BASE_DIR, path, task, lang))
    for one in dirs:
        os.makedirs(os.path.join(*one), exist_ok=True)
    return dirs

# build_dirs()
