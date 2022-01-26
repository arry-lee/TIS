from rich import print
from rich.console import Console
from rich.progress import track
import time

def do_step(step):
    time.sleep(0.1)


# for step in track(range(100)):
#     do_step(step)

import numpy as np

a = np.zeros((2,3))
print(a)

