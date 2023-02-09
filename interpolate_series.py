import argparse
from typing import Callable
from tqdm import tqdm
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from deep_interpolate import DeepInterpolate
from webui_utils.simple_log import SimpleLog
from webui_utils.file_utils import create_directory, get_files

def main():
    parser = argparse.ArgumentParser(description="Video Frame Interpolation (deep)")
    parser.add_argument("--model", default="./pretrained_models/pretrained_VFIformer/net_220.pth", type=str)
    parser.add_argument("--gpu_ids", type=str, default="0", help="gpu ids: e.g. 0  0,1,2, 0,2. use -1 for CPU")
    parser.add_argument("--input_path", default="./images", type=str, help="Input path for PNGs to interpolate")
    parser.add_argument("--depth", default=2, type=int, help="how many doublings of the frames")
    parser.add_argument("--output_path", default="./output", type=str, help="Output path for interpolated PNGs")
    parser.add_argument("--base_filename", default="interpolated_frames", type=str, help="Base filename for interpolated PNGs")
    parser.add_argument("--verbose", dest="verbose", default=False, action="store_true", help="Show extra details")
    args = parser.parse_args()

    log = SimpleLog(args.verbose)
    create_directory(args.output_path)
    engine = InterpolateEngine(args.model, args.gpu_ids)
    interpolater = Interpolate(engine.model, log.log)
    deep_interpolater = DeepInterpolate(interpolater, log.log)
    series_interpolater = InterpolateSeries(deep_interpolater, log.log)

    file_list = get_files(args.input_path, extension="png")
    series_interpolater.interpolate_series(file_list, args.output_path, args.depth, args.base_filename)

class InterpolateSeries():
    def __init__(self,
                deep_interpolater : DeepInterpolate,
                log_fn : Callable | None):
        self.deep_interpolater = deep_interpolater

    def interpolate_series(self, file_list : list, output_path : str, num_splits : int, base_filename : str):
        file_list = sorted(file_list)
        count = len(file_list)
        num_width = len(str(count))

        pbar_desc = "Frames" if num_splits < 2 else "Total"
        # stop short of beginning at the last frame since there's no frame after i
        for frame in tqdm(range(count-1), desc=pbar_desc, position=0):
            # for other than the first around, the duplicated real "before" frame is deleted for
            # continuity, since it's identical to the "after" from the previous round
            continued = frame > 0
            before_file = file_list[frame]
            after_file = file_list[frame+1]
            filename = base_filename + "[" + str(frame).zfill(num_width) + "]"
            inner_bar_desc = f"Frame #{frame}"
            self.deep_interpolater.split_frames(before_file, after_file, num_splits, output_path, filename, progress_label=inner_bar_desc, continued=continued)

if __name__ == '__main__':
    main()
