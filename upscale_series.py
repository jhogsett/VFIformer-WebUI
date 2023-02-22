"""Upscale Frames Core Code"""
import argparse
import glob
import os
from typing import Callable
import cv2
from basicsr.archs.rrdbnet_arch import RRDBNet# pylint: disable=import-error
from basicsr.utils.download_util import load_file_from_url# pylint: disable=import-error
from realesrgan import RealESRGANer # pylint: disable=import-error
from realesrgan.archs.srvgg_arch import SRVGGNetCompact # pylint: disable=import-error
from tqdm import tqdm
from webui_utils.simple_log import SimpleLog
from webui_utils.file_utils import create_directory, get_files

def main():
    """Use Upscale Frames from the command line"""
    parser = argparse.ArgumentParser(description="Video Frame Upscaling (Real-ESRGAN)")
    parser.add_argument("--model_name", default="RealESRGAN_x4plus", type=str,
        help="Name of Real-ESRGAN model")
    parser.add_argument("--gpu_ids", type=str, default="0",
        help="gpu ids: e.g. 0  0,1,2, 0,2. use -1 for CPU")
    parser.add_argument("--input_path", default="./images", type=str,
        help="Input path for PNGs to upscale")
    parser.add_argument("--output_path", default="./output", type=str,
        help="Output path for upscaled PNGs")
    parser.add_argument("--outscale", type=float, default=4.0,
        help="The final upsampling scale of the image 1.0-8.0")
    parser.add_argument("--base_filename", default="upscaled_frames", type=str,
        help="Base filename for upsampled PNGs")
    parser.add_argument(
        "--fp32", action="store_true",
        help="Use fp32 precision during inference. Default: fp16 (half precision).")
    parser.add_argument("--verbose", dest="verbose", default=False, action="store_true",
        help="Show extra details")
    args = parser.parse_args()

    log = SimpleLog(args.verbose)
    create_directory(args.output_path)
    file_list = get_files(args.input_path, extension="png")
    upscaler = UpscaleSeries(args.model_name, args.gpu_ids, args.fp32, log.log)
    upscaler.upscale_series(file_list, args.outout_path, args.outscale, args.base_filename)

class UpscaleSeries():
    """Encapsulates logic for the Upscale Frames feature"""
    def __init__(self,
                model_name : str,
                gpu_ids : str | None,
                fp32 : bool,
                log_fn : Callable | None):
        self.upscaler =  self.load_upscaler(model_name, gpu_ids, fp32)
        self.log_fn = log_fn

    def upscale_series(self,
                        file_list : list,
                        output_path : str,
                        outscale : float,
                        base_filename):
        """Invoke the Upscale Frames feature"""
        file_list = sorted(file_list)
        count = len(file_list)
        num_width = len(str(count))
        pbar_desc = "Frame"

        for index, filepath in enumerate(tqdm(file_list, desc=pbar_desc, position=0)):
            output_filename = f"{base_filename}{str(index).zfill(num_width)}.png"
            output_filepath = os.path.join(output_path, output_filename)
            self.log(f"upscaling by {outscale} {filepath} to {output_filepath}")
            self.upscale_image(filepath, output_filepath, outscale)

    def upscale_image(self,
                        input_filepath : str,
                        output_filepath : str,
                        outscale : float):
        img = cv2.imread(input_filepath, cv2.IMREAD_UNCHANGED)
        try:
            output, _ = self.upscaler.enhance(img, outscale=outscale)
            cv2.imwrite(output_filepath, output)
        except RuntimeError as error:
            print('Real-ESRGAN Error', error)

    def load_upscaler(self, model_name : str, gpu_ids : str | None, fp32 : bool):
        """determine models according to model names"""
        model_name = model_name.split('.')[0]
        if model_name == 'RealESRGAN_x4plus':  # x4 RRDBNet model
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32,
                scale=4)
            netscale = 4
            file_url = \
        ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth']
        elif model_name == 'RealESRNet_x4plus':  # x4 RRDBNet model
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32,
                scale=4)
            netscale = 4
            file_url = \
        ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.1/RealESRNet_x4plus.pth']
        elif model_name == 'RealESRGAN_x4plus_anime_6B':  # x4 RRDBNet model with 6 blocks
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32,
                scale=4)
            netscale = 4
            file_url = \
['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth']
        elif model_name == 'RealESRGAN_x2plus':  # x2 RRDBNet model
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32,
                scale=2)
            netscale = 2
            file_url = \
        ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth']
        elif model_name == 'realesr-animevideov3':  # x4 VGG-style model (XS size)
            model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=4,
                act_type='prelu')
            netscale = 4
            file_url = \
    ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth']
        elif model_name == 'realesr-general-x4v3':  # x4 VGG-style model (S size)
            model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4,
                act_type='prelu')
            netscale = 4
            file_url = [
'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth',
'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth'
            ]
        model_path = os.path.join('weights', model_name + '.pth')
        if not os.path.isfile(model_path):
            ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
            for url in file_url:
                # model_path will be updated
                model_path = load_file_from_url(url=url,
                    model_dir=os.path.join(ROOT_DIR, 'weights'), progress=True, file_name=None)

        # defaults in place of unoffered options
        dni_weight = 0.5
        tile = 0
        tile_pad = 10
        pre_pad = 0
        return RealESRGANer(
            scale=netscale,
            model_path=model_path,
            dni_weight=dni_weight,
            model=model,
            tile=tile,
            tile_pad=tile_pad,
            pre_pad=pre_pad,
            half=not fp32,
            gpu_id=gpu_ids)

    def log(self, message):
        """Logging"""
        if self.log_fn:
            self.log_fn(message)

if __name__ == '__main__':
    main()
