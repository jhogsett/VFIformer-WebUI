import os
import argparse
import shutil
from typing import Callable
from tqdm import tqdm
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from interpolation_target import TargetInterpolate
from restore_frames import RestoreFrames
from webui_utils.simple_log import SimpleLog
from webui_utils.file_utils import create_directory, get_files

def main():
    parser = argparse.ArgumentParser(description="Video Frame Interpolation - Upsample Video")
    parser.add_argument("--model", default="./pretrained_models/pretrained_VFIformer/net_220.pth", type=str)
    parser.add_argument("--gpu_ids", type=str, default="0", help="gpu ids: e.g. 0  0,1,2, 0,2. use -1 for CPU")
    parser.add_argument("--input_path", default="./images", type=str, help="Input path for PNGs to interpolate")
    parser.add_argument("--num_frames", default=2, type=int, help="Number of frames to fill")
    parser.add_argument("--depth", default=10, type=int, help="How deep the frame splits go to reach the target")
    parser.add_argument("--output_path", default="./output", type=str, help="Output path for interpolated PNGs")
    parser.add_argument("--base_filename", default="upsampled_frames", type=str, help="Base filename for interpolated PNGs")
    parser.add_argument("--verbose", dest="verbose", default=False, action="store_true", help="Show extra details")
    args = parser.parse_args()

    log = SimpleLog(args.verbose)
    create_directory(args.output_path)
    engine = InterpolateEngine(args.model, args.gpu_ids)
    interpolater = Interpolate(engine.model, log.log)
    target_interpolater = TargetInterpolate(interpolater, log.log)
    frame_restorer = RestoreFrames(target_interpolater, log.log)
    series_upsampler = UpsampleSeries(frame_restorer, log.log)

    series_upsampler.upsample_series(args.input_path, args.output_path, args.num_frames, args.depth, args.base_filename)

class UpsampleSeries():
    def __init__(self,
                frame_restorer : RestoreFrames,
                log_fn : Callable | None):
        self.frame_restorer = frame_restorer
        self.log_fn = log_fn
        self.output_paths = []

    def log(self, message):
        if self.log_fn:
            self.log_fn(message)

    def upsample_series(self, input_path : str, output_path : str, num_frames : int, num_splits : int, base_filename : str, offset : int = 1):
        file_list = sorted(get_files(input_path, "png"))
        count = len(file_list)
        num_width = len(str(count))
        pbar_desc = "Frames" if num_splits < 2 else "Total"

        # this is three levels of pbars and it doesn't look great but acceptable
        # the position= argument never seems to make a difference
        for n in tqdm(range(count - offset), desc=pbar_desc, position=0):
            before_file = file_list[n]
            after_file = file_list[n + offset]
            base_index = n
            filename = base_filename + "[" + str(base_index).zfill(num_width) + "]"

            # copy the original frame before the filler frames
            keyframe_filename = f"{filename}@0.0.png"
            self.log(f"creating keyframe file for frame files {before_file} - {after_file}")
            shutil.copy(before_file, os.path.join(output_path, keyframe_filename))

            inner_bar_desc = f"Frame #{n}"
            self.log(f"creating upsampled frames for frame files {before_file} - {after_file}")
            self.frame_restorer.restore_frames(before_file, after_file, num_frames, num_splits, output_path, filename, progress_label=inner_bar_desc)
            self.output_paths.extend(self.frame_restorer.output_paths)

if __name__ == '__main__':
    main()
