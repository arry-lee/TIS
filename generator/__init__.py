import functools


class BaseGenerator:
    """各类图片生成器基类"""

    def __init__(self, name):
        self.name = name

    def run(self, product_engine, **kwargs):
        """
        运行方法，无需重写
        :param product_engine: 假数据引擎
        :param lang: 语言
        :return: image_dict
        """
        template = self.load_template(**kwargs)
        self.preprocess(template)
        image_data = self.render_template(template, product_engine)
        image_data = self.postprocess(image_data, **kwargs)
        return image_data

    def preprocess(self, template):
        """模板预处理钩子，不同类型的预处理可能有所不同，原地处理"""

    # pylint: disable=unused-argument no-self-use
    def postprocess(self, image_data, **kwargs):
        """
        后处理钩子，不同的类型后处理可能有不同的后处理模式
        :param image_data: dict
        :return: dict
        """
        return image_data

    def render_template(self, template, engine):
        """
        模板渲染钩子
        :param template: 模板
        :param engine: 模板渲染引擎
        :return: imagedict
        """
        return NotImplemented

    def load_template(self, **kwargs):
        """模板加载钩子"""
        return NotImplemented


class ImagePipe:
    
    def __init__(self,function):
        self.function = function
        functools.update_wrapper(self, function)
        
    def __or__(self, other):
        return self.function(other)

    def __call__(self, *args, **kwargs):
        print(f'calling {self.function.__name__}')
        return self.function(*args,**kwargs)

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
        return Pipe(lambda x:self.function(other.function(x)))

    def __call__(self,image, *args, **kwargs):
        return self.function(image,*args,**kwargs)


@Pipe
def f(x,a=3):
    print('f')
    return x+x+a

@Pipe
def g(x):
    print('g')
    return x*3

print((f|g)(3))
