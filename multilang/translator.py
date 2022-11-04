import random
from functools import lru_cache
from hashlib import md5

import requests
from translatepy import Translator as T


class Translator(T):
    def __init__(self, to_lang, from_lang="zh"):
        super().__init__(fast=True)
        self.from_lang = from_lang
        self.to_lang = to_lang
    
    def translate(self, text):
        return super().translate(text, self.to_lang, self.from_lang)


BAIDU_TRANS_MAP = {'id'   : 'id', 'fil_PH': 'fil', 'nl_be': 'nl', 'cs': 'cs',
                   'el_GR': 'el', 'bn': 'ben', 'ne': 'nep', 'si': 'sin',
                   'km'   : 'hkm', 'lo_LA': 'lao', 'ms_MY': 'may'}


def get_code(code):
    if code in BAIDU_TRANS_MAP:
        return BAIDU_TRANS_MAP.get(code)
    return code


class BaiduTranslator:
    
    def __init__(self, to_lang, from_lang="zh"):
        self.appid = '20190913000334110'  # '20220815001307359'
        self.appkey = 'FqMjEsfJxLw2yea6u1kv'  # '7KUQFH6DnV7W4wbIWc4F'
        self.endpoint = 'http://api.fanyi.baidu.com'
        self.path = '/api/trans/vip/translate'
        self.from_lang = get_code(from_lang)
        self.to_lang = get_code(to_lang)
        print(self.to_lang)
    
    @lru_cache
    def translate(self, text):
        """use cache to store result"""
        salt = random.randint(32768, 65536)
        str_sign = self.appid + text + str(salt) + self.appkey
        sign = BaiduTranslator.make_md5(str_sign)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'appid': self.appid, 'q': text, 'from': self.from_lang,
                   'to'   : self.to_lang, 'salt': salt, 'sign': sign}
        url = self.endpoint + self.path
        # Send request
        response = requests.post(url, params=payload, headers=headers)
        result = response.json()
        dst_list = []
        try:
            for dst in result['trans_result']:
                dst_list.append(dst['dst'])
        except KeyError:
            raise KeyError(str(result))
        
        return ''.join(dst_list)
    
    @staticmethod
    def make_md5(s, encoding='utf-8'):
        return md5(s.encode(encoding)).hexdigest()


if __name__ == '__main__':
    keys = ["NIK", "Nama", "Tempat/Tgl Lahir", "Sems Kelamin", "Alamat",
            "RT/RW", "Kel/Desa", "Kecamatan", "Agama"
                                              "Status Perkawinan",
            "MINAHASA SELATAN", "Pekerjaan", "Kerwaganegaraan", "Berlaku Hingga"
            ]
    t = BaiduTranslator(from_lang='id', to_lang='zh')
    for key in keys:
        w = t.translate(key)
        print(key, w)
