import threading
import itertools
import time
import sys
import subprocess

nums = """
 ██████╗ 
██╔═████╗
██║██╔██║
████╔╝██║
╚██████╔╝
 ╚═════╝ 

 ██╗
███║
╚██║
 ██║
 ██║
 ╚═╝

██████╗ 
╚════██╗
 █████╔╝
██╔═══╝ 
███████╗
╚══════╝

██████╗ 
╚════██╗
 █████╔╝
 ╚═══██╗
██████╔╝
╚═════╝ 

██╗  ██╗
██║  ██║
███████║
╚════██║
     ██║
     ╚═╝

███████╗
██╔════╝
███████╗
╚════██║
███████║
╚══════╝

 ██████╗ 
██╔════╝ 
███████╗ 
██╔═══██╗
╚██████╔╝
 ╚═════╝ 

███████╗
╚════██║
   ██╔╝ 
  ██╔╝  
  ██║   
  ╚═╝   

 █████╗ 
██╔══██╗
╚█████╔╝
██╔══██╗
╚█████╔╝
 ╚════╝ 

 █████╗ 
██╔══██╗
╚██████║
 ╚═══██║
 █████╔╝
 ╚════╝ 
"""


s1 = """
██╗  ██╗███████╗██╗     ██╗      ██████╗     ██████╗  ██████╗ ██████╗  ██╗
██║  ██║██╔════╝██║     ██║     ██╔═══██╗    ╚════██╗██╔═████╗╚════██╗███║
███████║█████╗  ██║     ██║     ██║   ██║     █████╔╝██║██╔██║ █████╔╝╚██║
██╔══██║██╔══╝  ██║     ██║     ██║   ██║    ██╔═══╝ ████╔╝██║██╔═══╝  ██║
██║  ██║███████╗███████╗███████╗╚██████╔╝    ███████╗╚██████╔╝███████╗ ██║
╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝ ╚═════╝     ╚══════╝ ╚═════╝ ╚══════╝ ╚═╝

"""
s = """
██╗  ██╗███████╗██╗     ██╗      ██████╗     ██████╗  ██████╗ ██████╗ ██████╗ 
██║  ██║██╔════╝██║     ██║     ██╔═══██╗    ╚════██╗██╔═████╗╚════██╗╚════██╗
███████║█████╗  ██║     ██║     ██║   ██║     █████╔╝██║██╔██║ █████╔╝ █████╔╝
██╔══██║██╔══╝  ██║     ██║     ██║   ██║    ██╔═══╝ ████╔╝██║██╔═══╝ ██╔═══╝ 
██║  ██║███████╗███████╗███████╗╚██████╔╝    ███████╗╚██████╔╝███████╗███████╗
╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝ ╚═════╝     ╚══════╝ ╚═════╝ ╚══════╝╚══════╝
"""


def hello2022(signal):
    write, flush = sys.stdout.write, sys.stdout.flush
    for num in itertools.cycle(nums.split("\n\n")):
        write(num)
        subprocess.run("cls", shell=True)
        if not signal.go:
            break
    write(s)


class Signal:
    go = True


def counter_down(t):
    write, flush = sys.stdout.write, sys.stdout.flush
    for char in itertools.cycle(range(t)):
        l = write(str(char))
        flush()
        write("\x08" * l)
        time.sleep(0.1)


def spin(msg, signal):
    write, flush = sys.stdout.write, sys.stdout.flush
    for char in itertools.cycle("|/-\\"):
        status = char + " " + msg
        write(status)
        flush()
        write("\x08" * len(status))
        time.sleep(0.1)
        if not signal.go:
            break
    write(" " * len(status) + "\x08" * len(status))


def slow_function():
    time.sleep(3)
    return 42


def supervisor():
    signal = Signal()
    spinner = threading.Thread(target=spin, args=(signal,))
    spinner.start()
    result = slow_function()
    signal.go = False
    spinner.join()
    return result


def main():
    result = supervisor()
    print("Answer:", result)


if __name__ == "__main__":
    main()
