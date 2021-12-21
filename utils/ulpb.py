from pypinyin import lazy_pinyin, Style

XIAOHE = {'ai': 'd', 'an': 'j', 'ang': 'h', 'ao': 'c', 'ch': 'i', 'ei': 'w',
          'en': 'f', 'eng': 'g', 'i': 'i', 'ia': 'x', 'ian': 'm', 'iang': 'l',
          'iao': 'n',
          'ie': 'p', 'in': 'b', 'ing': 'k', 'iong': 's', 'iu': 'q', 'ong': 's',
          'ou': 'z',
          'sh': 'u', 'u': 'u', 'ua': 'x', 'uai': 'k', 'uan': 'r', 'uang': 'l',
          'ue': 't',
          'ui': 'v', 'un': 'y', 'uo': 'o', 've': 't', 'zh': 'v'}

STYLE_CHOICES = {'XIAOHE': XIAOHE}


def isvowel(pinyin):
    return pinyin[0] in 'aoe'


def _split(pinyin):
    # 分割拼音,返回 声母，韵母，声调 元组
    if isvowel(pinyin):
        return ('', pinyin[:-1], pinyin[-1])
    if pinyin[1] == 'h':
        return pinyin[:2], pinyin[2:-1], pinyin[-1]
    return pinyin[0], pinyin[1:-1], pinyin[-1]


def shuangpin(pinyin, style='XIAOHE', tone=False):
    """ 将拼音转换为双拼.

    :param pinyin: 汉字拼音
    :type pinyin: str 
    :param style: 指定双拼风格，默认是小鹤双拼风格。
                  更多拼音风格详见 :class:`~pypinyin.Style`。
    :param tone: 指定是否需要声调
    :return: 双拼字符串
    :rtype: str

	"""
    table = STYLE_CHOICES.get(style, None)
    if table is None:  raise ValueError('No Such Style')
    if len(pinyin) == 1: return pinyin * 2  # aoe
    if len(pinyin) == 2: return pinyin  # li lv qu an ai en

    try:
        s, y, t = _split(pinyin)
        if s == '':  # ang
            s = y[0]
        elif len(s) == 2:
            s = table[s]
        if len(y) > 1:
            y = table[y]
        if tone is False:
            t = ''
    except KeyError:
        return pinyin
    return s + y + t


def is_chinese(ch):
    if '\u4e00' <= ch <= '\u9fff':
        return True
    return False


def encode(hans, style='XIAOHE', tone=False):
    """ 将汉字转换为双拼编码.

    :param hans: 汉字
    :type hans: unicode or list
    :param style: 指定双拼风格，默认是小鹤双拼风格。
                  更多拼音风格详见 :class:`~pypinyin.Style`。
    :param tone: 指定是否需要声调,12345
    :return: 双拼字符串
    :rtype: str

	"""
    return str.upper(''.join(shuangpin(x, style=style, tone=tone) \
                             for x in lazy_pinyin(hans, style=Style.TONE3,
                                                  neutral_tone_with_five=True)))
