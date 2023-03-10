"""Core Code for all frame interpolations"""
import argparse
import math
from typing import Callable
import cv2
import torch
import torchvision
from webui_utils.simple_log import SimpleLog
from interpolate_engine import InterpolateEngine

def main():
    """Use Frame Interpolation from the command line"""
    parser = argparse.ArgumentParser(description='Video Frame Interpolation (shallow)')
    parser.add_argument('--model',
        default='./pretrained_models/pretrained_VFIformer/net_220.pth', type=str)
    parser.add_argument('--gpu_ids', type=str, default='0',
        help='gpu ids: e.g. 0  0,1,2, 0,2. use -1 for CPU')
    parser.add_argument('--img_before', default="./images/image0.png", type=str,
        help="Path to before frame image")
    parser.add_argument('--img_after', default="./images/image2.png", type=str,
        help="Path to after frame image")
    parser.add_argument('--img_new', default="./images/image1.png", type=str,
        help="Path to new middle frame image")
    parser.add_argument("--verbose", dest="verbose", default=False, action="store_true",
        help="Show extra details")
    args = parser.parse_args()

    log = SimpleLog(args.verbose)
    engine = InterpolateEngine(args.model, args.gpu_ids)
    interpolater = Interpolate(engine.model, log.log)
    interpolater.create_between_frame(args.img_before, args.img_after, args.img_new)

class Interpolate:
    """Encapsulate logic for the Frame Interpolation feature"""
    def __init__(self,
                model,
                log_fn : Callable | None):
        self.model = model
        self.log_fn = log_fn

    def create_between_frame(self,
                            before_filepath : str,
                            after_filepath : str,
                            middle_filepath : str):
        """Invoke the Frame Interpolation feature"""

        # code borrowed from VFIformer/demo.py
        img0 = cv2.imread(before_filepath)
        img1 = cv2.imread(after_filepath)

        divisor = 64
        height, width, _ = img0.shape
        if height % divisor != 0 or width % divisor != 0:
            h_new = math.ceil(height / divisor) * divisor
            w_new = math.ceil(width / divisor) * divisor
            pad_t = (h_new - height) // 2
            pad_d = (h_new - height) // 2 + (h_new - height) % 2
            pad_l = (w_new - width) // 2
            pad_r = (w_new - width) // 2 + (w_new - width) % 2
            img0 = cv2.copyMakeBorder(img0.copy(), pad_t, pad_d, pad_l, pad_r,
                cv2.BORDER_CONSTANT, value=0)  # cv2.BORDER_REFLECT
            img1 = cv2.copyMakeBorder(img1.copy(), pad_t, pad_d, pad_l, pad_r,
                cv2.BORDER_CONSTANT, value=0)
        else:
            pad_t, pad_d, pad_l, pad_r = 0, 0, 0, 0

        img0 = torch.from_numpy(img0.astype('float32') / 255.).float().permute(2, 0, 1).cuda()\
            .unsqueeze(0)
        img1 = torch.from_numpy(img1.astype('float32') / 255.).float().permute(2, 0, 1).cuda()\
            .unsqueeze(0)

        with torch.no_grad():
            output, _ = self.model(img0, img1, None)
            height, width = output.size()[2:]
            output = output[:, :, pad_t:height-pad_d, pad_l:width-pad_r]

        imt = output[0].flip(dims=(0,)).clamp(0., 1.)
        torchvision.utils.save_image(imt, middle_filepath)
        self.log("create_mid_frame() saved " + middle_filepath)

    def log(self, message):
        """Logging"""
        if self.log_fn:
            self.log_fn(message)

if __name__ == '__main__':
    main()
