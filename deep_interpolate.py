import os
import cv2
import argparse
from tqdm import tqdm
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from webui_utils.simple_log import SimpleLog
from webui_utils.simple_utils import max_steps
from webui_utils.file_utils import create_directory
from typing import Callable

def main():
    parser = argparse.ArgumentParser(description="Video Frame Interpolation (deep)")
    parser.add_argument("--model", default="./pretrained_models/pretrained_VFIformer/net_220.pth", type=str)
    parser.add_argument("--gpu_ids", type=str, default="0", help="gpu ids: e.g. 0  0,1,2, 0,2. use -1 for CPU")
    parser.add_argument("--img_before", default="./images/image0.png", type=str, help="Path to before frame image")
    parser.add_argument("--img_after", default="./images/image2.png", type=str, help="Path to after frame image")
    parser.add_argument("--depth", default=2, type=int, help="how many doublings of the frames")
    parser.add_argument("--output_path", default="./output", type=str, help="Output path for interpolated PNGs")
    parser.add_argument("--base_filename", default="interpolated_frame", type=str, help="Base filename for interpolated PNGs")
    parser.add_argument("--verbose", dest="verbose", default=False, action="store_true", help="Show extra details")
    args = parser.parse_args()

    log = SimpleLog(args.verbose)
    create_directory(args.output_path)
    engine = InterpolateEngine(args.model, args.gpu_ids)
    interpolater = Interpolate(engine.model, log.log)
    deep_interpolater = DeepInterpolate(interpolater, log.log)
    deep_interpolater.split_frames(args.img_before, args.img_after, args.depth, args.output_path, args.base_filename)

class DeepInterpolate():
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
                    before_filepath, 
                    after_filepath, 
                    num_splits, 
                    output_path, 
                    base_filename, 
                    progress_label="Frame", 
                    continued=False):
        self.init_frame_register()
        self.reset_split_manager(num_splits)
        num_steps = max_steps(num_splits)
        self.init_progress(num_splits, num_steps, progress_label)
        output_filepath_prefix = os.path.join(output_path, base_filename)
        self.set_up_outer_frames(before_filepath, after_filepath, output_filepath_prefix)

        self.recursive_split_frames(0.0, 1.0, output_filepath_prefix)
        self.integerize_filenames(output_path, base_filename, continued)
        self.close_progress()

    def recursive_split_frames(self,
                                first_index : float, 
                                last_index : float, 
                                filepath_prefix : str):
        if self.enter_split():
            mid_index = first_index + (last_index - first_index) / 2.0
            first_filepath = self.indexed_filepath(filepath_prefix, first_index)
            last_filepath = self.indexed_filepath(filepath_prefix, last_index)
            mid_filepath = self.indexed_filepath(filepath_prefix, mid_index)

            self.interpolater.create_between_frame(first_filepath, last_filepath, mid_filepath)
            self.register_frame(mid_filepath)
            self.step_progress()

            # deal with two new split regions
            self.recursive_split_frames(first_index, mid_index, filepath_prefix)
            self.recursive_split_frames(mid_index, last_index, filepath_prefix)
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

    def integerize_filenames(self, output_path, base_name, continued):
        file_prefix = os.path.join(output_path, base_name)
        frame_files = self.sorted_registered_frames()
        num_width = len(str(len(frame_files)))
        index = 0
        self.output_paths = []

        for file in frame_files:
            if continued and index == 0:
                # if a continuation from a previous set of frames, delete the first frame
                # to maintain continuity since it's duplicate of the previous round last frame
                os.remove(file)
                self.log("removed uneeded " + file)
            else:
                new_filename = file_prefix + str(index).zfill(num_width) + ".png"
                os.replace(file, new_filename)
                self.output_paths.append(new_filename)
                self.log("renamed " + file + " to " + new_filename)
            index += 1

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

    def sorted_registered_frames(self):
        return sorted(self.frame_register)

    def init_progress(self, num_splits, max, description):
        if num_splits < 2:
            self.progress = None
        else:
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
        return filepath_prefix + f"{index:1.24f}.png"


if __name__ == '__main__':
    main()
