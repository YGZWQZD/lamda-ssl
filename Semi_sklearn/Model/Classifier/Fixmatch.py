import copy
from Semi_sklearn.Base.InductiveEstimator import InductiveEstimator
from Semi_sklearn.Base.SemiDeepModelMixin import SemiDeepModelMixin
from sklearn.base import ClassifierMixin

import torch.nn.functional as F

import torch

def interleave(x, size):
    s = list(x.shape)
    return x.reshape([-1, size] + s[1:]).transpose(0, 1).reshape([-1] + s[1:])

def de_interleave(x, size):
    s = list(x.shape)
    return x.reshape([size, -1] + s[1:]).transpose(0, 1).reshape([-1] + s[1:])

class Fixmatch(InductiveEstimator,SemiDeepModelMixin,ClassifierMixin):
    def __init__(self,train_dataset=None,test_dataset=None,
                 train_dataloader=None,
                 test_dataloader=None,
                 augmentation=None,
                 network=None,
                 train_sampler=None,
                 train_batch_sampler=None,
                 test_sampler=None,
                 test_batch_sampler=None,
                 epoch=1,
                 num_it_epoch=None,
                 num_it_total=None,
                 eval_epoch=None,
                 eval_it=None,
                 optimizer=None,
                 scheduler=None,
                 device='cpu',
                 evaluation=None,
                 threshold=None,
                 lambda_u=None,
                 mu=None,
                 ema_decay=None,
                 T=None,
                 weight_decay=None
                 ):
        SemiDeepModelMixin.__init__(self,train_dataset=train_dataset,
                                    test_dataset=test_dataset,
                                    train_dataloader=train_dataloader,
                                    test_dataloader=test_dataloader,
                                    augmentation=augmentation,
                                    network=network,
                                    train_sampler=train_sampler,
                                    train_batch_sampler=train_batch_sampler,
                                    test_sampler=test_sampler,
                                    test_batch_Sampler=test_batch_sampler,
                                    epoch=epoch,
                                    num_it_epoch=num_it_epoch,
                                    num_it_total=num_it_total,
                                    eval_epoch=eval_epoch,
                                    eval_it=eval_it,
                                    mu=mu,
                                    weight_decay=weight_decay,
                                    ema_decay=ema_decay,
                                    optimizer=optimizer,
                                    scheduler=scheduler,
                                    device=device,
                                    evaluation=evaluation
                                    )
        self.lambda_u=lambda_u
        self.threshold=threshold
        self.T=T
        self.weight_decay=weight_decay
        self._estimator_type=ClassifierMixin._estimator_type

    def train(self,lb_X,lb_y,ulb_X,lb_idx=None,ulb_idx=None,*args,**kwargs):
        w_lb_X=self.weakly_augmentation.fit_transform(lb_X)
        w_ulb_X=self.weakly_augmentation.fit_transform(ulb_X)
        s_ulb_X=self.strongly_augmentation.fit_transform(ulb_X)
        batch_size = w_lb_X.shape[0]
        inputs=torch.cat((w_lb_X, w_ulb_X, s_ulb_X))
        inputs = interleave(inputs, 2 * self.mu + 1)
        logits = self._network(inputs)
        logits = de_interleave(logits, 2 * self.mu + 1)
        logits_x = logits[:batch_size]
        logits_u_w, logits_u_s = logits[batch_size:].chunk(2)
        result=(logits_x,lb_y,logits_u_w,logits_u_s)
        return result

    def get_loss(self,train_result,*args,**kwargs):
        logits_x, lb_y, logits_u_w, logits_u_s = train_result
        Lx = F.cross_entropy(logits_x, lb_y, reduction='mean')

        pseudo_label = torch.softmax(logits_u_w.detach() / self.T, dim=-1)
        max_probs, targets_u = torch.max(pseudo_label, dim=-1)
        mask = max_probs.ge(self.threshold).float()

        Lu = (F.cross_entropy(logits_u_s, targets_u,
                              reduction='none') * mask).mean()

        loss = Lx + self.lambda_u * Lu
        return loss

    def predict(self,X=None):
        return SemiDeepModelMixin.predict(self,X=X)

