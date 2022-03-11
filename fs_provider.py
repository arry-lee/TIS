import glob
import os
from faker.providers.lorem import Provider as LoremProvider


def _read_words_from_dir(basedir):
    # 读取标注文件夹内的所有label文本并分词
    out = []
    texts = glob.glob(os.path.join(basedir, '**/*.txt'))
    for ino, text_file in enumerate(texts):
        with open(text_file, 'r', encoding='utf-8') as f:
            for line in f:
                _, s = line.split('@', 1)
                words = s.split()
                out.extend(words)
    return out


FINANCIAL_WORD_LIST = _read_words_from_dir('static/label')


class Provider(LoremProvider):
    word_list = FINANCIAL_WORD_LIST


if __name__ == '__main__':
    from faker import Faker
    f = Faker(providers=['fs_provider'])
    print(f.paragraph())
