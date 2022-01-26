import os
os.environ['UNRAR_LIB_PATH']= r'C:\Program Files (x86)\UnrarDLL\x64\UnRAR64.dll'
import re

import requests
import tqdm
from unrar import rarfile

font_pat = re.compile(r'<a href="/fonts/(\d+.html)"')
rar_pat = re.compile(r"https.+?rar",re.A)

headers =\
    """
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
"""
headers = dict(x.split(': ', 1) for x in headers.splitlines() if x)


def get_font_list(page_no):
    page_url = 'https://www.jb51.net/fonts/list425_%d.html'%page_no
    r = requests.get(page_url,headers=headers)
    # print(r.text)
    if r.ok:
        ms = re.findall(font_pat,r.text)

        for m in list(set(ms[1:])):
            font_url = 'https://www.jb51.net/fonts/' + m
            print(font_url)
            download_font(font_url)


def get_font_link(font_url):
    r = requests.get(font_url,headers=headers)
    if r.ok:
        font_page = r.text
        # print(font_page)
        ms = re.findall(rar_pat,font_page)
        if not ms:
            print(ms)
            return
        # print(ms)
        with open('x.txt', 'a',encoding='utf-8') as f:
            for m in ms:
                f.write(m+'\n')
            # fonts.append(ms)
    else:
        raise Exception

    # r = requests.get(ms[1],headers=headers)
    # if r.ok:
    #     fn = ms[1].split('/')[-1]
    #     print(fn)
    #     with open(fn,'wb') as f:
    #         f.write(r.content)
    # else:
    #     raise Exception


def download_font(url):
    r = requests.get(url, headers=headers)
    if r.ok:
        fn = url.split('/')[-1]
        with open(fn,'wb') as f:
            f.write(r.content)
    else:
        return False
    return True

def readwrite():
    from collections import defaultdict
    d = defaultdict(set)
    with open('x.txt') as f:
        for line in f:
            url = line.strip()
            p,name = url.rsplit('/',1)
            d[name].add(url)

    print(len(d))

    with open('url.txt', 'w') as f:
        for k,v in d.items():
            f.write(k+'\n')
            for s in v:
                f.write(s+'\n')
            f.write('\n')


def extract(zip):
    rar = rarfile.RarFile(zip)
    # print(rar.namelist())
    for f in rar.namelist():
        if f.endswith('ttf'):
            rar.extract(f)
            print(f)


import pickle
def main():
    from collections import defaultdict
    d = defaultdict(set)
    with open('x.txt') as f:
        for line in f:
            url = line.strip()
            p,name = url.rsplit('/',1)
            d[name].add(url)

    if not os.path.exists('download.pkl'):
        downloaded = set()
    else:
        with open('download.pkl','rb') as f:
            downloaded = pickle.load(f)

    for k, v in tqdm.tqdm(d.items()):
        try:
            flag = False
            if not k in downloaded:
                for url in v:
                    try:
                        flag = download_font(url)
                        if flag:
                            break
                    except:
                        continue
                if flag:
                    extract(k)
                    os.remove(k)
                    downloaded.add(k)
        except Exception as e:
            with open('download.pkl', 'wb') as f:
                pickle.dump(downloaded,f)
            raise e


if __name__ == '__main__':
    main()