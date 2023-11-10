import os.path

import numpy as np
import torch
from PIL import Image

from .src import model

import torchvision.transforms.functional as tf

BASE_DIR = os.path.dirname(__file__)
DEFAULT_MODEL_PATH = os.path.join(BASE_DIR, "pretrained/harmonizer.pth")


class Harmonizer:
    """和谐器包装"""

    def __init__(self, pretrained=None, cuda=False):
        """和谐器是个单例"""
        if not pretrained:
            pretrained = DEFAULT_MODEL_PATH
        harmonizer = model.Harmonizer()
        if cuda:
            harmonizer = harmonizer.cuda()
            map_location = None
        else:
            map_location = "cpu"
        harmonizer.load_state_dict(
            torch.load(pretrained, map_location=map_location), strict=True
        )
        harmonizer.eval()
        self.harmonizer = harmonizer
        self.cuda = cuda

    def __call__(self, comp, mask):
        """
        使得生成的图像更和谐
        Args:
            comp: 合成图
            mask: 合成图的前景 mask

        Returns:

        """
        comp = tf.to_tensor(comp)[None, ...]
        mask = tf.to_tensor(mask)[None, ...]

        if self.cuda:
            comp = comp.cuda()
            mask = mask.cuda()

        with torch.no_grad():
            arguments = self.harmonizer.predict_arguments(comp, mask)
            harmonized = self.harmonizer.restore_image(comp, mask, arguments)

        harmonized = np.transpose(harmonized[0].cpu().numpy(), (1, 2, 0)) * 255
        return Image.fromarray(harmonized.astype(np.uint8))


harmonize = Harmonizer()
