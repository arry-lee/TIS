import glob
import linecache
import os
from collections import defaultdict

from multifaker.providers.lorem import Provider as LoremProvider

cur_dir = os.path.split(os.path.abspath(__file__))[0]


class Provider(LoremProvider):
    """Implement lorem provider for ``si`` locale."""

    word_list = linecache.getlines(os.path.join(cur_dir, "wordlist.txt"))
    image_list = glob.glob(
        os.path.join(LoremProvider.base_images_dir, "malay", "full", "*.jpg")
    )
    word_map = defaultdict(list)
    for w in word_list:
        word_map[len(w.strip())].append(w.strip())
