import concurrent.futures
# 异步执行器,比自己创建线程池方便多了,I/O密集型操作线程池是很有用的
# 计算密集型的可以用ProcessPoolExecutor，不过max_worker不用设置
#  future 对象 - 代表异步执行指令
import time


import atexit
# 退出程序时必然会执行的代码
@atexit.register
def print_bye():
    print('BYE')


def wait(t):
    time.sleep(t)
    return t

start = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as exe:
    for a in exe.map(wait,range(1,5)):
        print(a)

print(time.time()-start)


