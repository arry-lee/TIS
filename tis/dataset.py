import os
import sys

from torch.utils.data.dataset import Dataset

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

sys.path.append(PROJECT_DIR)

from register import IMAGE_GENERATOR_REGISTRY
import numpy as np
from multifaker import Faker
# class IterableDataset(Dataset[T_co]):
#     r"""An iterable Dataset.
#
#     All datasets that represent an iterable of data samples should subclass it.
#     Such form of datasets is particularly useful when data come from a stream.
#
#     All subclasses should overwrite :meth:`__iter__`, which would return an
#     iterator of samples in this dataset.
#
#     When a subclass is used with :class:`~torch.utils.data.DataLoader`, each
#     item in the dataset will be yielded from the :class:`~torch.utils.data.DataLoader`
#     iterator. When :attr:`num_workers > 0`, each worker process will have a
#     different copy of the dataset object, so it is often desired to configure
#     each copy independently to avoid having duplicate data returned from the
#     workers. :func:`~torch.utils.data.get_worker_info`, when called in a worker
#     process, returns information about the worker. It can be used in either the
#     dataset's :meth:`__iter__` method or the :class:`~torch.utils.data.DataLoader` 's
#     :attr:`worker_init_fn` option to modify each copy's behavior.
#
#     Example 1: splitting workload across all workers in :meth:`__iter__`::
#
#         >>> class MyIterableDataset(torch.utils.data.IterableDataset):
#         ...     def __init__(self, start, end):
#         ...         super(MyIterableDataset).__init__()
#         ...         assert end > start, "this example code only works with end >= start"
#         ...         self.start = start
#         ...         self.end = end
#         ...
#         ...     def __iter__(self):
#         ...         worker_info = torch.utils.data.get_worker_info()
#         ...         if worker_info is None:  # single-process data loading, return the full iterator
#         ...             iter_start = self.start
#         ...             iter_end = self.end
#         ...         else:  # in a worker process
#         ...             # split workload
#         ...             per_worker = int(math.ceil((self.end - self.start) / float(worker_info.num_workers)))
#         ...             worker_id = worker_info.id
#         ...             iter_start = self.start + worker_id * per_worker
#         ...             iter_end = min(iter_start + per_worker, self.end)
#         ...         return iter(range(iter_start, iter_end))
#         ...
#         >>> # should give same set of data as range(3, 7), i.e., [3, 4, 5, 6].
#         >>> ds = MyIterableDataset(start=3, end=7)
#
#         >>> # Single-process loading
#         >>> print(list(torch.utils.data.DataLoader(ds, num_workers=0)))
#         [3, 4, 5, 6]
#
#         >>> # Mult-process loading with two worker processes
#         >>> # Worker 0 fetched [3, 4].  Worker 1 fetched [5, 6].
#         >>> print(list(torch.utils.data.DataLoader(ds, num_workers=2)))
#         [3, 5, 4, 6]
#
#         >>> # With even more workers
#         >>> print(list(torch.utils.data.DataLoader(ds, num_workers=20)))
#         [3, 4, 5, 6]
#
#     Example 2: splitting workload across all workers using :attr:`worker_init_fn`::
#
#         >>> class MyIterableDataset(torch.utils.data.IterableDataset):
#         ...     def __init__(self, start, end):
#         ...         super(MyIterableDataset).__init__()
#         ...         assert end > start, "this example code only works with end >= start"
#         ...         self.start = start
#         ...         self.end = end
#         ...
#         ...     def __iter__(self):
#         ...         return iter(range(self.start, self.end))
#         ...
#         >>> # should give same set of data as range(3, 7), i.e., [3, 4, 5, 6].
#         >>> ds = MyIterableDataset(start=3, end=7)
#
#         >>> # Single-process loading
#         >>> print(list(torch.utils.data.DataLoader(ds, num_workers=0)))
#         [3, 4, 5, 6]
#         >>>
#         >>> # Directly doing multi-process loading yields duplicate data
#         >>> print(list(torch.utils.data.DataLoader(ds, num_workers=2)))
#         [3, 3, 4, 4, 5, 5, 6, 6]
#
#         >>> # Define a `worker_init_fn` that configures each dataset copy differently
#         >>> def worker_init_fn(worker_id):
#         ...     worker_info = torch.utils.data.get_worker_info()
#         ...     dataset = worker_info.dataset  # the dataset copy in this worker process
#         ...     overall_start = dataset.start
#         ...     overall_end = dataset.end
#         ...     # configure the dataset to only process the split workload
#         ...     per_worker = int(math.ceil((overall_end - overall_start) / float(worker_info.num_workers)))
#         ...     worker_id = worker_info.id
#         ...     dataset.start = overall_start + worker_id * per_worker
#         ...     dataset.end = min(dataset.start + per_worker, overall_end)
#         ...
#
#         >>> # Mult-process loading with the custom `worker_init_fn`
#         >>> # Worker 0 fetched [3, 4].  Worker 1 fetched [5, 6].
#         >>> print(list(torch.utils.data.DataLoader(ds, num_workers=2, worker_init_fn=worker_init_fn)))
#         [3, 5, 4, 6]
#
#         >>> # With even more workers
#         >>> print(list(torch.utils.data.DataLoader(ds, num_workers=20, worker_init_fn=worker_init_fn)))
#         [3, 4, 5, 6]
#     """
#     def __iter__(self) -> Iterator[T_co]:
#         raise NotImplementedError
#
#     def __add__(self, other: Dataset[T_co]):
#         return ChainDataset([self, other])


class TISDataset(Dataset):
    """与具体的生成器类型无关的部分
   如果生成图像数据的过程比较耗时，那么在线生成数据可能会导致训练过程变慢，甚至无法进行有效训练。
   此外，如果数据生成速度跟不上模型训练的速度，也容易出现内存占用过多的问题。
   在线生成数据集可能会增加训练过程中的负担，尤其是当数据集较大或者数据生成过程复杂耗时时。
   相比之下，离线生成数据集并将生成好的数据保存到文件中，可以在训练过程中更快速地加载数据，减少数据生成对训练过程的影响。
   你可以考虑在训练之前将数据集离线生成并保存到文件中，然后在训练过程中直接从文件中加载数据。
   这样可以有效减轻训练过程中的负担，并且有助于避免内存占用过多的问题。

    """

    def __init__(self, name, size, lang='zh_CN', transforms=None):
        self._post_processors = []
        self.name = name
        self.generator = IMAGE_GENERATOR_REGISTRY.get(name)(name)
        self.engine = Faker  # 引擎类型
        self.size = size
        self.lang = lang
        self.transforms = transforms
        super().__init__()

    def __len__(self):
        return self.size

    def __getitem__(self, item):
        lang = self.lang
        product_engine = self.engine(lang)  # 各个语言有一个引擎实例

        image_data = self.generator.run(
            product_engine, lang=lang
        )
        # 后处理
        if self._post_processors:
            self.postprocess(image_data)

        # image_data['image'] = PILToTensor()(image_data['image'])
        keys = list(image_data.keys())

        image_data = TISLabelEncode()(image_data)
        for k in keys:
            if k not in ('image', 'polys', 'texts', "ignore_tags"):
                del image_data[k]
        image_data = self.transforms(image_data)
        return image_data

    def postprocess(self, image_data):
        """后处理器钩子

        :param image_data: 图片字典
        :param fname: 命名
        :param product_dir: 保存文件夹
        :return:
        """
        for proc_dict in self._post_processors:
            processor = proc_dict.get("func")
            image_data = processor(image_data)


class TISLabelEncode:
    def __init__(self, **kwargs):
        pass

    def __call__(self, data):
        label = data["label"]
        point = data["points"]
        nBox = len(label)
        boxes, txts, txt_tags = [], [], []
        for bno in range(0, nBox):
            box = point[bno * 4:bno * 4 + 4]  # 可能要扁平化
            # bx = [ ]
            # for x in box:
            #     bx.append(x[0])
            #     bx.append(x[1])

            txt = label[bno].removeprefix("text@")
            boxes.append(box)
            txts.append(txt)
        boxes = np.array(boxes, dtype=np.float32)
        txt_tags = np.array(txt_tags, dtype=bool)

        data["polys"] = boxes
        data["texts"] = txts
        data["ignore_tags"] = txt_tags

        return data

    def order_points_clockwise(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        tmp = np.delete(pts, (np.argmin(s), np.argmax(s)), axis=0)
        diff = np.diff(np.array(tmp), axis=1)
        rect[1] = tmp[np.argmin(diff)]
        rect[3] = tmp[np.argmax(diff)]
        return rect

    def expand_points_num(self, boxes):
        max_points_num = 0
        for box in boxes:
            if len(box) > max_points_num:
                max_points_num = len(box)
        ex_boxes = []
        for box in boxes:
            ex_box = box + [box[-1]] * (max_points_num - len(box))
            ex_boxes.append(ex_box)
        return ex_boxes
