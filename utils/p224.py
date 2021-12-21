import os
import glob

def _p224(basedir):
    # 两点标注转换为四点标注
    texts = glob.glob(os.path.join(basedir,'**/*.txt'))
    for ino,text_file in enumerate(texts):
        new_fn = text_file+'.bak'
        with open(text_file,'r',encoding='utf-8') as f2:
            with open(new_fn, 'w', encoding='utf-8') as f4:
                for line in f2:
                    try: # 防止破坏四点标注
                        l,t,r,b,label = line.split(';')
                        line = ';'.join([l, t, r, t, r, b, l, b, label])
                    except:
                        pass
                    finally:
                        f4.write(line)
        print('%d/%d>>>'%(ino+1,len(texts)),text_file)
        os.remove(text_file)
        os.rename(new_fn,text_file)