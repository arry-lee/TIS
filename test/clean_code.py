import glob
import os.path

ignore_files = ['__init__.py','p224.py','clean_code.py','fs_data.py','font_downloader.py']

with open('out.txt','w',encoding='utf-8') as outfp:
    for file in glob.glob('../**/*.py',recursive=True):
        if os.path.split(file)[1] in ignore_files:
            continue
        outfp.write('# ' + file[3:] + '\n\n')
        with open(file,'r',encoding='utf-8') as f:
            for line in f:
                if line.strip() == '':
                    outfp.write(line)
                elif line.strip()[0] == '#':
                    continue
                elif '#' in line:
                    outfp.write(line.split('#')[0]+'\n')
                else:
                    outfp.write(line)
        outfp.write('\n\n')