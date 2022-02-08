from Semi_sklearn.Data_Augmentation.Augmentation import Augmentation
import torchvision.transforms.functional as F
import random
import torch
import PIL

class Color(Augmentation):
    def __init__(self, min_v,max_v,num_bins,magnitude,v=None):
        super().__init__()
        self.max_v=max_v
        self.min_v=min_v
        self.num_bins=num_bins
        self.magnitude=magnitude
        self.magnitudes=torch.linspace(min_v, max_v, num_bins)
        self.v=float(self.magnitudes[self.magnitude].item())if v is None else v


    def transform(self,X):
        if isinstance(X,PIL.Image.Image):
            _v = self.v if random.random() < 0.5 else self.v * -1
            X=PIL.ImageEnhance.Color(X).enhance(1.0+_v)
            return X
        elif isinstance(X,torch.Tensor):
            if len(X.shape)==4:
                for _ in range(X.shape[0]):
                    _v = self.v if random.random() < 0.5 else self.v * -1
                    X[_]=F.adjust_saturation(X[_],1.0+_v)
            else:
                _v = self.v if random.random() < 0.5 else self.v * -1
                X = F.adjust_saturation(X,1.0+_v)
            return X
        else:
            raise ValueError('No data to augment')