import glob
import os
import re
import tqdm


def double_variable_name(text_file):
    new_fn = text_file + ".bak"
    with open(text_file, "r", encoding="utf-8") as f2:
        content = f2.read()
        content = r.sub(r"\1_\2\3", content)
        with open(new_fn, "w", encoding="utf-8") as f4:
            f4.write(content)
    os.remove(text_file)
    os.rename(new_fn, text_file)


def normalize(basedir):
    global r
    if os.path.isdir(basedir):
        pys = glob.glob(os.path.join(basedir, "**/*.py"))
        for ino, text_file in enumerate(pys):
            double_variable_name(text_file)
            print("%d/%d>>>" % (ino + 1, len(pys)), text_file)
    elif basedir.endswith(".py"):
        double_variable_name(basedir)
    else:
        raise Exception("\s is neither dir nor .py file" % basedir)


def parse(err, pattern):
    errs = []
    with open(err, "r", encoding="utf-8") as f:
        for line in f:
            matched = pattern.match(line)
            errs.append((matched[1], matched[2], matched[3]))
    return errs


def normal(fno, line_no, x):
    bak = fno + ".bak"
    with open(bak, "w", encoding="utf-8") as f4:
        with open(fno, "r", encoding="utf-8") as f:
            for lno, line in enumerate(f, start=1):
                if lno == line_no:
                    rr = re.compile("[^a-zA-Z0-9_]*(" + x + r")[^a-zA-Z0-9_]")
                    print(rr)
                    newline = rr.sub(r"_\1_", line)
                    print(newline)
                    f4.write(newline)
                else:
                    f4.write(line)
    os.remove(fno)
    os.rename(bak, fno)


def main(err, pattern):
    for fno, lno, x in tqdm.tqdm(parse(err, pattern)):
        normal(fno, lno, x)


if __name__ == "__main__":
    rr = re.compile(r"xx(\w+)xx(\d+)xx(\w+)")
    err = "err.txt"
    main(err, rr)
    # import sys
    # basedir = sys.argv[1]
    # normalize(basedir)
    # normal('tst.py',5,'r')
