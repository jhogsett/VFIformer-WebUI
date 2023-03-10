"""Restore Frames Feature Core Code"""
import sys
import argparse
from typing import Callable
from tqdm import tqdm
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from interpolation_target import TargetInterpolate
from webui_utils.simple_log import SimpleLog
from webui_utils.file_utils import create_directory
from webui_utils.simple_utils import restored_frame_searches

def main():
    """Use the Frame Restoration feature from the command line"""
    parser = argparse.ArgumentParser(description="Video Frame Interpolation (deep)")
    parser.add_argument("--model",
        default="./pretrained_models/pretrained_VFIformer/net_220.pth", type=str)
    parser.add_argument("--gpu_ids", type=str, default="0",
        help="gpu ids: e.g. 0  0,1,2, 0,2. use -1 for CPU")
    parser.add_argument("--img_before", default="./images/image0.png", type=str,
        help="Path to image file before the damaged frames")
    parser.add_argument("--img_after", default="./images/image2.png", type=str,
        help="Path to image file after the damaged frames")
    parser.add_argument("--num_frames", default=2, type=int,
        help="Number of frames to restore")
    parser.add_argument("--depth", default=10, type=int,
        help="How deep the frame splits go to reach the target")
    parser.add_argument("--output_path", default="./output", type=str,
        help="Output path for interpolated PNGs")
    parser.add_argument("--base_filename", default="restored_frame", type=str,
        help="Base filename for interpolated PNGs")
    parser.add_argument("--verbose", dest="verbose", default=False, action="store_true",
        help="Show extra details")
    args = parser.parse_args()

    log = SimpleLog(args.verbose)
    create_directory(args.output_path)
    engine = InterpolateEngine(args.model, args.gpu_ids)
    interpolater = Interpolate(engine.model, log.log)
    target_interpolater = TargetInterpolate(interpolater, log.log)
    frame_restorer = RestoreFrames(target_interpolater, log.log)

    frame_restorer.restore_frames(args.img_before, args.img_after, args.num_frames,
        args.depth, args.output_path, args.base_filename)

class RestoreFrames():
    """Encapsulate logic for the Frame Restoration feature"""
    def __init__(self,
                target_interpolater : TargetInterpolate,
                log_fn : Callable | None):
        self.target_interpolater = target_interpolater
        self.log_fn = log_fn
        self.output_paths = []

    def restore_frames(self,
                    img_before : str,
                    img_after : str,
                    num_frames : int,
                    depth: int,
                    output_path : str,
                    base_filename : str,
                    progress_label="Frames"):
        """Invoke the Frame Restoration feature"""
        searches = restored_frame_searches(num_frames)
        for search in tqdm(searches, desc=progress_label):
            self.log(f"searching for frame {search}")
            self.target_interpolater.split_frames(img_before, img_after, depth, min_target=search,
                max_target=search + sys.float_info.epsilon, output_path=output_path,
                base_filename=base_filename, progress_label="Search")
        self.output_paths.extend(self.target_interpolater.output_paths)
        self.target_interpolater.output_paths = []

    def log(self, message):
        """Logging"""
        if self.log_fn:
            self.log_fn(message)

if __name__ == '__main__':
    main()
