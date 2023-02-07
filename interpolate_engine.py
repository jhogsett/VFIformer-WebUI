from torch.nn.parallel import DistributedDataParallel
from collections import OrderedDict
import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn
from models.modules import define_G
from webui_utils.simple_utils import FauxArgs

# Singleton class with the loaded VFIformer model
# model: path to model such as "./pretrained_models/pretrained_VFIformer/net_220.pth"
# gpu_ids: e.g. "0" "0,1,2, 0,2" use "-1" for CPU
class InterpolateEngine:
    def __new__(cls, model : str, gpu_ids : str):
        if not hasattr(cls, 'instance'):
            cls.instance = super(InterpolateEngine, cls).__new__(cls)
            cls.instance.init(model, gpu_ids)
        return cls.instance

    def init(self, model : str, gpu_ids: str):
        gpu_id_array = self.init_device(gpu_ids)
        self.model = self.init_model(model, gpu_id_array)

    def init_device(self, gpu_ids : str):
        # code borrowed from demo.py
        str_ids = gpu_ids.split(',')
        gpu_ids = []
        for str_id in str_ids:
            id = int(str_id)
            if id >= 0:
                gpu_ids.append(id)
        if len(gpu_ids) > 0:
            torch.cuda.set_device(gpu_ids[0])
        cudnn.benchmark = True
        return gpu_ids

    def init_model(self, model, gpu_id_array):
        # code borrowed from demo.py
        device = torch.device('cuda' if len(gpu_id_array) != 0 else 'cpu')
        args = FauxArgs(model = model,
                    gpu_ids = gpu_id_array,
                    device = device,
                    # needed in original downstream code
                    crop_size = 192,
                    dist = False,
                    rank = -1,
                    phase = "test",
                    resume_flownet = "",
                    net_name = "VFIformer")
        net = define_G(args)
        net = self.load_networks(net, model)
        net.eval()
        return net

    def load_networks(self, network, resume, strict=True):
        # code borrowed from demo.py
        load_path = resume
        if isinstance(network, nn.DataParallel) or isinstance(network, DistributedDataParallel):
            network = network.module
        load_net = torch.load(load_path, map_location=torch.device('cpu'))
        load_net_clean = OrderedDict()  # remove unnecessary 'module.'
        for k, v in load_net.items():
            if k.startswith('module.'):
                load_net_clean[k[7:]] = v
            else:
                load_net_clean[k] = v
        network.load_state_dict(load_net_clean, strict=strict)
        return network
