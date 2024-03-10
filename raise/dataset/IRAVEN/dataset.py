import os
import os.path as path
import h5py
import torch
from torch.utils.data import Dataset


class IRavenDataset(Dataset):
    def __init__(self, name='center_single', part='train', size=64, cache_root='cache', label=1.0):
        super(IRavenDataset, self).__init__()
        self.name = name
        self.part = part
        self.size = size
        self.cache_root = os.path.join(cache_root, 'I-RAVEN')
        if not self.check_cache():
            raise FileNotFoundError('Cached dataset file not found.')
        self.panel = None
        self.selection = None
        self.answer = None
        self.label = None
        self.label_rate = label if part == 'train' else 1.0
        self.enable_label = None
        self.sample = None
        self.num_data = None
        self.load_data_from_cache()
        self.prepare_data()

    def __getitem__(self, index):
        if self.label_rate is None:
            return self.sample[index], self.panel[index], self.selection[index], \
                   self.answer[index]
        else:
            return self.sample[index], self.panel[index], self.selection[index], \
                   self.answer[index], self.label[index]

    def __len__(self):
        return self.num_data

    def data_cache_root(self):
        return path.join(self.cache_root, self.name, '{}_{}.hdf5'.format(self.part, self.size))

    def check_cache(self):
        return path.exists(self.data_cache_root())

    def load_data_from_cache(self):
        with h5py.File(self.data_cache_root(), 'r') as f:
            self.panel = torch.from_numpy(f['panel'][:]).float() / 255.
            self.selection = torch.from_numpy(f['selection'][:]).float() / 255.
            self.answer = torch.from_numpy(f['answer'][:]).long()
            self.label = torch.from_numpy(f['label'][:]).long()
        self.num_data = self.panel.size(0)

    def prepare_data(self):
        answer = self.answer[..., None, None, None, None].expand(-1, 1, *self.selection.size()[2:])
        answer_panel = torch.gather(self.selection, 1, answer)
        self.sample = torch.cat([self.panel, answer_panel], 1)
        if self.label_rate is not None:
            num_wl = int(self.label_rate * self.sample.size(0))
            indices = torch.randperm(self.sample.size(0))[:num_wl]
            self.sample = self.sample[indices]
            self.panel = self.panel[indices]
            self.selection = self.selection[indices]
            self.answer = self.answer[indices]
            self.label = self.label[indices]
            self.num_data = self.panel.size(0)
