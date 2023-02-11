import os
import argparse
from typing import Callable
import re
import cv2
from tqdm import tqdm
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from webui_utils.simple_log import SimpleLog
from webui_utils.simple_utils import float_range_in_range
from webui_utils.file_utils import create_directory

def main():
    parser = argparse.ArgumentParser(description="Video Frame Interpolation to a specify time")
    parser.add_argument("--model", default="./pretrained_models/pretrained_VFIformer/net_220.pth", type=str)
    parser.add_argument("--gpu_ids", type=str, default="0", help="gpu ids: e.g. 0  0,1,2, 0,2. use -1 for CPU")
    parser.add_argument("--img_before", default="./images/image0.png", type=str, help="Path to before frame image")
    parser.add_argument("--img_after", default="./images/image2.png", type=str, help="Path to after frame image")
    parser.add_argument("--depth", default=10, type=int, help="How deep the frame splits go to reach the target")
    parser.add_argument("--min_target", default=0.333, type=float, help="Lower bound of target time")
    parser.add_argument("--max_target", default=0.334, type=float, help="Upper bound of target time")
    parser.add_argument("--output_path", default="./output", type=str, help="Output path for interpolated PNGs")
    parser.add_argument("--base_filename", default="interpolated_frame", type=str, help="Base filename for interpolated PNGs")
    parser.add_argument("--verbose", dest="verbose", default=False, action="store_true", help="Show extra details")
    args = parser.parse_args()

    log = SimpleLog(args.verbose)
    create_directory(args.output_path)
    engine = InterpolateEngine(args.model, args.gpu_ids)
    interpolater = Interpolate(engine.model, log.log)
    target_interpolater = TargetInterpolate(interpolater, log.log)
    target_interpolater.split_frames(args.img_before, args.img_after, args.depth, args.min_target, args.max_target, args.output_path, args.base_filename)

class TargetInterpolate():
    def __init__(self,
                interpolater : Interpolate,
                log_fn : Callable | None):
        self.interpolater = interpolater
        self.log_fn = log_fn
        self.split_count = 0
        self.frame_register = []
        self.progress = None
        self.output_paths = []

    def log(self, message):
        if self.log_fn:
            self.log_fn(message)

    def split_frames(self,
                    before_filepath : str,
                    after_filepath : str,
                    num_splits : int,
                    min_target : float,
                    max_target : float,
                    output_path : str,
                    base_filename : str,
                    progress_label="Split"):
        self.init_frame_register()
        self.reset_split_manager(num_splits)
        self.init_progress(num_splits, progress_label)

        output_filepath_prefix = os.path.join(output_path, base_filename)
        self.set_up_outer_frames(before_filepath, after_filepath, output_filepath_prefix)

        self.recursive_split_frames(0.0, 1.0, output_filepath_prefix, min_target, max_target)
        self.isolate_target_frame()
        self.close_progress()

    def recursive_split_frames(self,
                                first_index : float,
                                last_index : float,
                                filepath_prefix : str,
                                min_target : float,
                                max_target : float):
        if self.enter_split():
            mid_index = first_index + (last_index - first_index) / 2.0
            first_filepath = self.indexed_filepath(filepath_prefix, first_index)
            last_filepath = self.indexed_filepath(filepath_prefix, last_index)
            mid_filepath = self.indexed_filepath(filepath_prefix, mid_index)

            self.interpolater.create_between_frame(first_filepath, last_filepath, mid_filepath)
            self.register_frame(mid_filepath)
            self.step_progress()

            # no more work if the current first-last range is entirely within the target range
            if float_range_in_range(first_index, last_index, min_target, max_target):
                self.log(f"skipping, current split range {first_index},{last_index} is inside target range {min_target},{max_target}")
            else:
                # recurse into the half that gets closer to the target range
                if float_range_in_range(min_target, max_target, first_index, mid_index, use_midpoint=True):
                    self.recursive_split_frames(first_index, mid_index, filepath_prefix, min_target, max_target)
                elif float_range_in_range(min_target, max_target, mid_index, last_index, use_midpoint=True):
                    self.recursive_split_frames(mid_index, last_index, filepath_prefix, min_target, max_target)
                else:
                    self.log(f"skipping, unable to locate target {min_target},{max_target} within split ranges {first_index},{mid_index} and {mid_index},{last_index}")
            self.exit_split()

    def set_up_outer_frames(self,
                            before_file,
                            after_file,
                            output_filepath_prefix):
        img0 = cv2.imread(before_file)
        img1 = cv2.imread(after_file)

        # create outer 0.0 and 1.0 versions of original frames
        before_index, after_index = 0.0, 1.0
        before_file = self.indexed_filepath(output_filepath_prefix, before_index)
        after_file = self.indexed_filepath(output_filepath_prefix, after_index)

        cv2.imwrite(before_file, img0)
        self.register_frame(before_file)
        self.log("copied " + before_file)

        cv2.imwrite(after_file, img1)
        self.register_frame(after_file)
        self.log("copied " + after_file)

    def isolate_target_frame(self):
        frame_files = self.registered_frames()

        # the kept frame will be the last frame registered
        kept_file = frame_files.pop(-1)

        # duplicates of the kept file may have been created, ensure they're not present
        frame_files = [file for file in frame_files if file != kept_file]

        # remove other duplicates
        frame_files = list(set(frame_files))

        filepath, fvalue, ext = self.split_indexed_filepath(kept_file)
        new_kept_file = f"{filepath}@{fvalue}{ext}"
        os.replace(kept_file, new_kept_file)
        self.output_paths.append(new_kept_file)
        self.log("renamed " + kept_file + " to " + new_kept_file)

        for file in frame_files:
            os.remove(file)
            self.log("removed uneeded " + file)

    def reset_split_manager(self, num_splits : int):
        self.split_count = num_splits

    def enter_split(self):
        if self.split_count < 1:
            return False
        self.split_count -= 1
        return True

    def exit_split(self):
        self.split_count += 1

    def init_frame_register(self):
        self.frame_register = []

    def register_frame(self, filepath : str):
        self.frame_register.append(filepath)

    def registered_frames(self):
        return self.frame_register

    def sorted_registered_frames(self):
        return sorted(self.frame_register)

    def init_progress(self, max, description):
        self.progress = tqdm(range(max), desc=description)

    def step_progress(self):
        if self.progress:
            self.progress.update()
            self.progress.refresh()

    def close_progress(self):
        if self.progress:
            self.progress.close()

    # filepath prefix representing the split position while splitting
    def indexed_filepath(self, filepath_prefix, index):
        return filepath_prefix + f"{index:1.55f}.png"

    def split_indexed_filepath(self, filepath : str):
        regex = r"(.+)([1|0]\..+)(\..+$)"
        result = re.search(regex, filepath)
        if result:
            file_part = result.group(1)
            float_part = result.group(2)
            ext_part = result.group(3)
            return file_part, float(float_part), ext_part
        else:
            self.log("unable to split indexed filepath {filepath}")
            return None, 0.0, None

if __name__ == '__main__':
    main()
