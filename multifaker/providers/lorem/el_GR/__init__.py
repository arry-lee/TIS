import glob
import linecache
import os
from collections import defaultdict

from multifaker.providers.lorem import Provider as LoremProvider
from awesometable.awesometable import clean_chars

cur_dir = os.path.split(os.path.abspath(__file__))[0]


class Provider(LoremProvider):
    """Implement lorem provider for ``si`` locale."""

    word_list = linecache.getlines(os.path.join(cur_dir, "wordlist.txt"))
    font_list = ["arial", "arialbd", "arialbi", "ariali", "arialuni"]
    image_list = glob.glob(
        os.path.join(LoremProvider.base_images_dir, "greek", "full", "*.jpg")
    )
    word_map = defaultdict(list)
    for w in word_list:
        word = clean_chars(w.strip())
        word_map[len(word)].append(word)

    def words(self, nb=3, ext_word_list=None, unique=False):
        word_list = ext_word_list if ext_word_list else self.word_list
        if unique:
            return [
                clean_chars(word.strip())
                for word in self.random_sample(word_list, length=nb)
            ]
        return [
            clean_chars(word.strip())
            for word in self.random_choices(word_list, length=nb)
        ]
