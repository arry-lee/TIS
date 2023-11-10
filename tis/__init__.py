import functools


class ImagePipe:
    def __init__(self, function):
        self.function = function
        functools.update_wrapper(self, function)

    def __or__(self, other):
        return self.function(other)

    def __call__(self, *args, **kwargs):
        print(f"calling {self.function.__name__}")
        return self.function(*args, **kwargs)


class Pipe:
    """
    Represent a Pipeable Element :
    Described as :
    first = Pipe(lambda iterable: next(iter(iterable)))
    and used as :
    print [1, 2, 3] | first
    printing 1

    Or represent a Pipeable Function :
    It's a function returning a Pipe
    Described as :
    select = Pipe(lambda iterable, pred: (pred(x) for x in iterable))
    and used as :
    print [1, 2, 3] | select(lambda x: x * 2)
    # 2, 4, 6
    """

    def __init__(self, function):
        self.function = function
        functools.update_wrapper(self, function)

    def __or__(self, other):
        return Pipe(lambda x: self.function(other.function(x)))

    def __call__(self, image, *args, **kwargs):
        return self.function(image, *args, **kwargs)
