"""VFIformer Engine Encapsulation Class"""
from collections import OrderedDict
from torch.nn.parallel import DistributedDataParallel
import torch
from torch import nn
from torch.backends import cudnn
from models.modules import define_G # pylint: disable=import-error
from webui_utils.simple_utils import FauxArgs

class InterpolateEngine:
    """Singleton class encapsulating the VFIformer engine and related logic"""
    # model: path to model such as "./pretrained_models/pretrained_VFIformer/net_220.pth"
    # gpu_ids: e.g. "0" "0,1,2, 0,2" use "-1" for CPU
    def __new__(cls, model : str, gpu_ids : str):
        if not hasattr(cls, 'instance'):
            cls.instance = super(InterpolateEngine, cls).__new__(cls)
            cls.instance.init(model, gpu_ids)
        return cls.instance

    def init(self, model : str, gpu_ids: str):
        """Iniitalize the class by calling into VFIformer code"""
        gpu_id_array = self.init_device(gpu_ids)
        self.model = self.init_model(model, gpu_id_array)

    def init_device(self, gpu_ids : str):
        """VFIformer code from demo.py"""
        str_ids = gpu_ids.split(',')
        gpu_ids = []
        for str_id in str_ids:
            _id = int(str_id)
            if _id >= 0:
                gpu_ids.append(_id)
        if len(gpu_ids) > 0:
            torch.cuda.set_device(gpu_ids[0])
        cudnn.benchmark = True
        return gpu_ids

    def init_model(self, model, gpu_id_array):
        """VFIformer code from demo.py"""
        device = torch.device('cuda' if len(gpu_id_array) != 0 else 'cpu')
        args = FauxArgs(model = model,
                    gpu_ids = gpu_id_array,
                    device = device,
                    # needed in VFIformer downstream code
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
        """VFIformer code from demo.py"""
        load_path = resume
        if isinstance(network, nn.DataParallel) or isinstance(network, DistributedDataParallel):
            network = network.module
        load_net = torch.load(load_path, map_location=torch.device('cpu'))
        load_net_clean = OrderedDict()  # remove unnecessary 'module.'
        for key, val in load_net.items():
            if key.startswith('module.'):
                load_net_clean[key[7:]] = val
            else:
                load_net_clean[key] = val
        network.load_state_dict(load_net_clean, strict=strict)
        return network
