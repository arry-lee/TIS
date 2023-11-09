import os
import time


def log_label(fn, img, data):
    labels = data["label"]
    points = data["points"]
    with open(fn, "w", encoding="utf-8") as f:
        for pointz, label in zip(points, labels):
            xys = [img]
            for p in pointz.tolist():
                xys.append(int(p[0]))
                xys.append(int(p[1]))
            xys.append(label)
            line = ";".join(map(str, xys))
            f.write(line + "\n")


def save_data(data, output_dir):
    im = data["image"]
    fn = "0" + str(int(time.time() * 1000))[5:]
    im.save(os.path.join(output_dir, "%s.jpg" % fn))
    log_label(os.path.join(output_dir, "%s.txt" % fn), "%s.jpg" % fn, data)
