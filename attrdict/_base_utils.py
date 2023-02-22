import numpy as np
import torch


def is_array(arr):
    return isinstance(arr, np.ndarray) or isinstance(arr, torch.Tensor)
