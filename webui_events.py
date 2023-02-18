import os
import shutil
import math
import gradio as gr
from interpolate import Interpolate
from deep_interpolate import DeepInterpolate
from interpolate_series import InterpolateSeries
from webui_utils.auto_increment import AutoIncrementDirectory, AutoIncrementFilename
from webui_utils.image_utils import create_gif
from webui_utils.file_utils import create_zip, get_files, create_directory, locate_frame_file, split_filepath
from webui_utils.simple_utils import max_steps, restored_frame_fractions, restored_frame_predictions, fps_change_details
from webui_utils.video_utils import MP4toPNG, PNGtoMP4, QUALITY_SMALLER_SIZE, GIFtoPNG, PNGtoGIF
from resequence_files import ResequenceFiles
from interpolation_target import TargetInterpolate
from restore_frames import RestoreFrames
from video_blender import VideoBlenderState, VideoBlenderProjects
from create_ui import create_ui
from resample_series import ResampleSeries

class WebuiEvents:
    def __init__(self, engine, config, log):
        self.engine = engine
        self.config = config
        self.log = log
        self.video_blender_state = None
        self.video_blender_projects = VideoBlenderProjects(self.config.blender_settings["projects_file"])

    def frame_interpolation(self, img_before_file : str, img_after_file : str, num_splits : float):
        if img_before_file and img_after_file:
            interpolater = Interpolate(self.engine.model, self.log.log)
            deep_interpolater = DeepInterpolate(interpolater, self.log.log)
            base_output_path = self.config.directories["output_interpolation"]
            output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
            output_basename = "interpolated_frames"

            self.log.log(f"creating frame files at {output_path}")
            deep_interpolater.split_frames(img_before_file, img_after_file, num_splits, output_path, output_basename)
            output_paths = deep_interpolater.output_paths

            downloads = []
            preview_gif = None
            if self.config.interpolation_settings["create_gif"]:
                preview_gif = os.path.join(output_path, output_basename + str(run_index) + ".gif")
                self.log.log(f"creating preview file {preview_gif}")
                duration = self.config.interpolation_settings["gif_duration"] / len(output_paths)
                create_gif(output_paths, preview_gif, duration=duration)
                downloads.append(preview_gif)

            if self.config.interpolation_settings["create_zip"]:
                download_zip = os.path.join(output_path, output_basename + str(run_index) + ".zip")
                self.log.log("creating zip of frame files")
                create_zip(output_paths, download_zip)
                downloads.append(download_zip)

            if self.config.interpolation_settings["create_txt"]:
                info_file = os.path.join(output_path, output_basename + str(run_index) + ".txt")
                self.create_report(info_file, img_before_file, img_after_file, num_splits, output_path, output_paths)
                downloads.append(info_file)

            return gr.Image.update(value=preview_gif), gr.File.update(value=downloads, visible=True)
        else:
            return None, None

    def frame_search(self, img_before_file : str, img_after_file : str, num_splits : float, min_target : float, max_target : float):
        if img_before_file and img_after_file and min_target and max_target:
            interpolater = Interpolate(self.engine.model, self.log.log)
            target_interpolater = TargetInterpolate(interpolater, self.log.log)
            base_output_path = self.config.directories["output_search"]
            create_directory(base_output_path)
            output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
            output_basename = "frame"

            self.log.log(f"beginning targeted interpolations at {output_path}")
            target_interpolater.split_frames(img_before_file, img_after_file, num_splits, float(min_target), float(max_target), output_path, output_basename)
            output_paths = target_interpolater.output_paths
            return gr.Image.update(value=output_paths[0]), gr.File.update(value=output_paths, visible=True)

    def video_inflation(self, input_path : str, output_path : str | None, num_splits : float):
        if input_path:
            interpolater = Interpolate(self.engine.model, self.log.log)
            deep_interpolater = DeepInterpolate(interpolater, self.log.log)
            series_interpolater = InterpolateSeries(deep_interpolater, self.log.log)
            base_output_path = output_path or self.config.directories["output_inflation"]
            create_directory(base_output_path)
            output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
            output_basename = "interpolated_frames"
            file_list = get_files(input_path, extension="png")

            self.log.log(f"beginning series of deep interpolations at {output_path}")
            series_interpolater.interpolate_series(file_list, output_path, num_splits, output_basename)

    def resynthesize_video(self, input_path : str, output_path : str | None):
        if input_path:
            interpolater = Interpolate(self.engine.model, self.log.log)
            deep_interpolater = DeepInterpolate(interpolater, self.log.log)
            series_interpolater = InterpolateSeries(deep_interpolater, self.log.log)
            base_output_path = output_path or self.config.directories["output_resynthesis"]
            create_directory(base_output_path)
            output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
            output_basename = "resynthesized_frames"

            file_list = get_files(input_path, extension="png")
            self.log.log(f"beginning series of frame recreations at {output_path}")
            series_interpolater.interpolate_series(file_list, output_path, 1, output_basename, offset=2)
            self.log.log(f"auto-resequencing recreated frames at {output_path}")
            ResequenceFiles(output_path, "png", "resynthesized_frame", 1, 1, -1, True, self.log.log).resequence()

    def resequence_files(self, input_path : str, input_filetype : str, input_newname : str, input_start : str, input_step : str, input_zerofill : str, input_rename_check : bool):
        if input_path and input_filetype and input_newname and input_start and input_step and input_zerofill:
            ResequenceFiles(input_path, input_filetype, input_newname, int(input_start), int(input_step), int(input_zerofill), input_rename_check, self.log.log).resequence()

    def frame_restoration(self, img_before_file : str, img_after_file : str, num_frames : float, num_splits : float):
        if img_before_file and img_after_file:
            interpolater = Interpolate(self.engine.model, self.log.log)
            target_interpolater = TargetInterpolate(interpolater, self.log.log)
            frame_restorer = RestoreFrames(target_interpolater, self.log.log)
            base_output_path = self.config.directories["output_restoration"]
            create_directory(base_output_path)
            output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
            output_basename = "restored_frame"

            self.log.log(f"beginning frame restorations at {output_path}")
            frame_restorer.restore_frames(img_before_file, img_after_file, num_frames, num_splits, output_path, output_basename)
            output_paths = frame_restorer.output_paths

            downloads = []
            preview_gif = None
            if self.config.restoration_settings["create_gif"]:
                preview_gif = os.path.join(output_path, output_basename + str(run_index) + ".gif")
                self.log.log(f"creating preview file {preview_gif}")
                duration = self.config.restoration_settings["gif_duration"] / len(output_paths)
                gif_paths = [img_before_file, *output_paths, img_after_file]
                create_gif(gif_paths, preview_gif, duration=duration)
                downloads.append(preview_gif)

            if self.config.restoration_settings["create_zip"]:
                download_zip = os.path.join(output_path, output_basename + str(run_index) + ".zip")
                self.log.log("creating zip of frame files")
                create_zip(output_paths, download_zip)
                downloads.append(download_zip)

            if self.config.restoration_settings["create_txt"]:
                info_file = os.path.join(output_path, output_basename + str(run_index) + ".txt")
                self.create_report(info_file, img_before_file, img_after_file, num_splits, output_path, output_paths)
                downloads.append(info_file)

            return gr.Image.update(value=preview_gif), gr.File.update(value=downloads, visible=True)

    def video_blender_load(self, project_path, frames_path1, frames_path2):
        self.video_blender_state = VideoBlenderState(project_path, frames_path1, frames_path2)
        return gr.update(selected=1), 0, *self.video_blender_state.goto_frame(0)

    def video_blender_save_project(self, project_name : str, project_path : str, frames1_path : str, frames2_path : str):
        self.video_blender_projects.save_project(project_name, project_path, frames1_path, frames2_path)

    def video_blender_choose_project(self, project_name):
        if project_name:
            dictobj = self.video_blender_projects.load_project(project_name)
            if dictobj:
                return dictobj["project_name"], dictobj["project_path"], dictobj["frames1_path"], dictobj["frames2_path"]
        return

    def video_blender_prev_frame(self, frame : str):
        frame = int(frame)
        frame -= 1
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_next_frame(self, frame : str):
        frame = int(frame)
        frame += 1
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_goto_frame(self, frame : str):
        frame = int(frame)
        frame = 0 if frame < 0 else frame
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_skip_next(self, frame : str):
        frame = int(frame) + int(self.config.blender_settings["skip_frames"])
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_skip_prev(self, frame : str):
        frame = int(frame) - int(self.config.blender_settings["skip_frames"])
        frame = 0 if frame < 0 else frame
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_use_path1(self, frame : str):
        frame = int(frame)
        to_filepath = self.video_blender_state.get_frame_file(VideoBlenderState.PROJECT_PATH, frame)
        from_filepath = self.video_blender_state.get_frame_file(VideoBlenderState.FRAMES1_PATH, frame)
        self.log.log(f"copying {from_filepath} to {to_filepath}")
        shutil.copy(from_filepath, to_filepath)
        frame += 1
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_use_path2(self, frame : str):
        frame = int(frame)
        to_filepath = self.video_blender_state.get_frame_file(VideoBlenderState.PROJECT_PATH, frame)
        from_filepath = self.video_blender_state.get_frame_file(VideoBlenderState.FRAMES2_PATH, frame)
        self.log.log(f"copying {from_filepath} to {to_filepath}")
        shutil.copy(from_filepath, to_filepath)
        frame += 1
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_fix_frames(self, project_path : str, frame : float):
        return gr.update(selected=2), project_path, frame, frame

    def video_blender_preview_fixed(self, project_path : str, before_frame : int, after_frame : int):
        if project_path and after_frame > before_frame:
            interpolater = Interpolate(self.engine.model, self.log.log)
            target_interpolater = TargetInterpolate(interpolater, self.log.log)
            frame_restorer = RestoreFrames(target_interpolater, self.log.log)
            base_output_path = self.config.directories["output_blender"]
            create_directory(base_output_path)
            output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
            output_basename = "fixed_frames"

            before_file = locate_frame_file(project_path, before_frame)
            after_file = locate_frame_file(project_path, after_frame)
            num_frames = (after_frame - before_frame) - 1
            search_depth = int(self.config.blender_settings["frame_fixer_depth"])

            self.log.log(f"beginning frame fixes at {output_path}")
            frame_restorer.restore_frames(before_file, after_file, num_frames, search_depth, output_path, output_basename)
            output_paths = frame_restorer.output_paths

            preview_gif = os.path.join(output_path, output_basename + str(run_index) + ".gif")
            self.log.log(f"creating preview file {preview_gif}")
            duration = self.config.blender_settings["gif_duration"] / len(output_paths)
            gif_paths = [before_file, *output_paths, after_file]
            create_gif(gif_paths, preview_gif, duration=duration)

            return gr.Image.update(value=preview_gif), gr.Text.update(value=output_path, visible=True)

    def video_blender_used_fixed(self, project_path : str, fixed_frames_path : str, before_frame : int):
        fixed_frames = sorted(get_files(fixed_frames_path, "png"))
        frame = before_frame + 1
        for file in fixed_frames:
            project_file = locate_frame_file(project_path, frame)
            self.log.log(f"copying {file} to {project_file}")
            shutil.copy(file, project_file)
            frame += 1
        return gr.update(selected=1)

    def video_blender_preview_video(self, input_path : str):
        return gr.update(selected=3), input_path

    def video_blender_render_preview(self, input_path : str, frame_rate : int):
        output_filepath, run_index = AutoIncrementFilename(self.config.directories["working"], "mp4").next_filename("video_preview", "mp4")
        ffmpeg_cmd = PNGtoMP4(input_path, "auto", int(frame_rate), output_filepath, crf=QUALITY_SMALLER_SIZE)
        return output_filepath

    def convert_mp4_to_png(self, input_filepath : str, output_pattern : str, frame_rate : int, output_path: str):
        if input_filepath and output_pattern and output_path:
            create_directory(output_path)
            ffmpeg_cmd = MP4toPNG(input_filepath, output_pattern, int(frame_rate), output_path)
            return gr.update(value=ffmpeg_cmd, visible=True)

    def convert_png_to_mp4(self, input_path : str, input_pattern : str, frame_rate : int, output_filepath: str, quality : str):
        if input_path and input_pattern and output_filepath:
            directory, _, _ = split_filepath(output_filepath)
            create_directory(directory)
            ffmpeg_cmd = PNGtoMP4(input_path, input_pattern, int(frame_rate), output_filepath, crf=quality)
            return gr.update(value=ffmpeg_cmd, visible=True)

    def convert_gif_to_png(self, input_filepath : str, output_path : str):
        if input_filepath and output_path:
            create_directory(output_path)
            ffmpeg_cmd = GIFtoPNG(input_filepath, output_path)
            return gr.update(value=ffmpeg_cmd, visible=True)

    def convert_png_to_gif(self, input_path : str, input_pattern : str, output_filepath : str):
        if input_path and input_pattern and output_filepath:
            directory, _, _ = split_filepath(output_filepath)
            create_directory(directory)
            ffmpeg_cmd = PNGtoGIF(input_path, input_pattern, output_filepath)
            return gr.update(value=ffmpeg_cmd, visible=True)

    def convert_fc(self, input_path : str, output_path : str, starting_fps : int, ending_fps : int, precision : int):
        if input_path:
            interpolater = Interpolate(self.engine.model, self.log.log)
            target_interpolater = TargetInterpolate(interpolater, self.log.log)
            series_resampler = ResampleSeries(target_interpolater, self.log.log)
            if output_path:
                base_output_path = output_path
                create_directory(base_output_path)
            else:
                base_output_path, _ = AutoIncrementDirectory(self.config.directories["output_fps_change"]).next_directory("run")
            series_resampler.resample_series(input_path, base_output_path, starting_fps, ending_fps, precision, f"resampled@{starting_fps}")

            self.log.log(f"auto-resequencing sampled frames at {output_path}")
            ResequenceFiles(base_output_path, "png", f"resampled@{ending_fps}fps", 0, 1, -1, True, self.log.log).resequence()

    #### UI Helpers

    def update_splits_info(self, num_splits : float):
        return str(max_steps(num_splits))

    def update_info_fr(self, num_frames : int, num_splits : int):
        fractions = restored_frame_fractions(num_frames)
        predictions = restored_frame_predictions(num_frames, num_splits)
        return fractions, predictions

    def update_info_fc(self, starting_fps : int, ending_fps : int, precision : int):
        return fps_change_details(starting_fps, ending_fps, precision)

    def create_report(self, info_file : str, img_before_file : str, img_after_file : str, num_splits : int, output_path : str, output_paths : list):
        report = f"""before file: {img_before_file}
    after file: {img_after_file}
    number of splits: {num_splits}
    output path: {output_path}
    frames:
    """ + "\n".join(output_paths)
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(report)
