import os
import shutil
import time
import signal
import argparse
import math
import gradio as gr
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from deep_interpolate import DeepInterpolate
from interpolate_series import InterpolateSeries
from webui_utils.simple_log import SimpleLog
from webui_utils.simple_config import SimpleConfig
from webui_utils.auto_increment import AutoIncrementDirectory, AutoIncrementFilename
from webui_utils.image_utils import create_gif
from webui_utils.file_utils import create_directories, create_zip, get_files, create_directory, locate_frame_file, split_filepath
from webui_utils.simple_utils import max_steps, restored_frame_fractions, restored_frame_predictions
from webui_utils.video_utils import MP4toPNG, PNGtoMP4, QUALITY_SMALLER_SIZE, GIFtoPNG, PNGtoGIF
from resequence_files import ResequenceFiles
from interpolation_target import TargetInterpolate
from restore_frames import RestoreFrames
from video_blender import VideoBlenderState, VideoBlenderProjects
from create_ui import create_ui
from upsample_series import UpsampleSeries

log = None
config = None
engine= None
restart = False
prevent_inbrowser = False
video_blender_state = None
video_blender_projects = None

def main():
    global log, config, engine, prevent_inbrowser, video_blender_projects
    parser = argparse.ArgumentParser(description='VFIformer Web UI')
    parser.add_argument("--config_path", type=str, default="config.yaml", help="path to config YAML file")
    parser.add_argument("--verbose", dest="verbose", default=False, action="store_true", help="Show extra details")
    args = parser.parse_args()

    log = SimpleLog(args.verbose)
    config = SimpleConfig(args.config_path).config_obj()
    create_directories(config.directories)

    while True:
        engine = InterpolateEngine(config.model, config.gpu_ids)

        print("Starting VFIformer-WebUI")
        print("Please be patient, the models are loaded on the first interpolation")

        video_blender_projects = VideoBlenderProjects(config.blender_settings["projects_file"])
        app = setup_ui(config, video_blender_projects)
        app.launch(inbrowser = config.auto_launch_browser and not prevent_inbrowser,
                    server_name = config.server_name,
                    server_port = config.server_port,
                    prevent_thread_lock=True)

        # idea borrowed from stable-diffusion-webui webui.py
        # after initial launch, disable inbrowser for subsequent restarts
        prevent_inbrowser = True

        wait_on_server(app)
        print("Restarting...")

#### Gradio UI event handlers

def frame_interpolation(img_before_file : str, img_after_file : str, num_splits : float):
    global log, config, engine
    if img_before_file and img_after_file:
        interpolater = Interpolate(engine.model, log.log)
        deep_interpolater = DeepInterpolate(interpolater, log.log)
        base_output_path = config.directories["output_interpolation"]
        output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
        output_basename = "interpolated_frames"

        log.log(f"creating frame files at {output_path}")
        deep_interpolater.split_frames(img_before_file, img_after_file, num_splits, output_path, output_basename)
        output_paths = deep_interpolater.output_paths

        downloads = []
        preview_gif = None
        if config.interpolation_settings["create_gif"]:
            preview_gif = os.path.join(output_path, output_basename + str(run_index) + ".gif")
            log.log(f"creating preview file {preview_gif}")
            duration = config.interpolation_settings["gif_duration"] / len(output_paths)
            create_gif(output_paths, preview_gif, duration=duration)
            downloads.append(preview_gif)

        if config.interpolation_settings["create_zip"]:
            download_zip = os.path.join(output_path, output_basename + str(run_index) + ".zip")
            log.log("creating zip of frame files")
            create_zip(output_paths, download_zip)
            downloads.append(download_zip)

        if config.interpolation_settings["create_txt"]:
            info_file = os.path.join(output_path, output_basename + str(run_index) + ".txt")
            create_report(info_file, img_before_file, img_after_file, num_splits, output_path, output_paths)
            downloads.append(info_file)

        return gr.Image.update(value=preview_gif), gr.File.update(value=downloads, visible=True)
    else:
        return None, None

def frame_search(img_before_file : str, img_after_file : str, num_splits : float, min_target : float, max_target : float):
    global log, config, engine
    if img_before_file and img_after_file and min_target and max_target:
        interpolater = Interpolate(engine.model, log.log)
        target_interpolater = TargetInterpolate(interpolater, log.log)
        base_output_path = config.directories["output_search"]
        create_directory(base_output_path)
        output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
        output_basename = "frame"

        log.log(f"beginning targeted interpolations at {output_path}")
        target_interpolater.split_frames(img_before_file, img_after_file, num_splits, float(min_target), float(max_target), output_path, output_basename)
        output_paths = target_interpolater.output_paths
        return gr.Image.update(value=output_paths[0]), gr.File.update(value=output_paths, visible=True)

def video_inflation(input_path : str, output_path : str | None, num_splits : float):
    global log, config, engine, file_output
    if input_path:
        interpolater = Interpolate(engine.model, log.log)
        deep_interpolater = DeepInterpolate(interpolater, log.log)
        series_interpolater = InterpolateSeries(deep_interpolater, log.log)
        base_output_path = output_path or config.directories["output_inflation"]
        create_directory(base_output_path)
        output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
        output_basename = "interpolated_frames"
        file_list = get_files(input_path, extension="png")

        log.log(f"beginning series of deep interpolations at {output_path}")
        series_interpolater.interpolate_series(file_list, output_path, num_splits, output_basename)

def resynthesize_video(input_path : str, output_path : str | None):
    global log, config, engine, file_output
    if input_path:
        interpolater = Interpolate(engine.model, log.log)
        deep_interpolater = DeepInterpolate(interpolater, log.log)
        series_interpolater = InterpolateSeries(deep_interpolater, log.log)
        base_output_path = output_path or config.directories["output_resynthesis"]
        create_directory(base_output_path)
        output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
        output_basename = "resynthesized_frames"

        file_list = get_files(input_path, extension="png")
        log.log(f"beginning series of frame recreations at {output_path}")
        series_interpolater.interpolate_series(file_list, output_path, 1, output_basename, offset=2)
        log.log(f"auto-resequencing recreated frames at {output_path}")
        ResequenceFiles(output_path, "png", "resynthesized_frame", 1, 1, -1, True, log.log).resequence()

def resequence_files(input_path : str, input_filetype : str, input_newname : str, input_start : str, input_step : str, input_zerofill : str, input_rename_check : bool):
    global log
    if input_path and input_filetype and input_newname and input_start and input_step and input_zerofill:
        ResequenceFiles(input_path, input_filetype, input_newname, int(input_start), int(input_step), int(input_zerofill), input_rename_check, log.log).resequence()

def frame_restoration(img_before_file : str, img_after_file : str, num_frames : float, num_splits : float):
    global log, config, engine, file_output
    if img_before_file and img_after_file:
        interpolater = Interpolate(engine.model, log.log)
        target_interpolater = TargetInterpolate(interpolater, log.log)
        frame_restorer = RestoreFrames(target_interpolater, log.log)
        base_output_path = config.directories["output_restoration"]
        create_directory(base_output_path)
        output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
        output_basename = "restored_frame"

        log.log(f"beginning frame restorations at {output_path}")
        frame_restorer.restore_frames(img_before_file, img_after_file, num_frames, num_splits, output_path, output_basename)
        output_paths = frame_restorer.output_paths

        downloads = []
        preview_gif = None
        if config.restoration_settings["create_gif"]:
            preview_gif = os.path.join(output_path, output_basename + str(run_index) + ".gif")
            log.log(f"creating preview file {preview_gif}")
            duration = config.restoration_settings["gif_duration"] / len(output_paths)
            gif_paths = [img_before_file, *output_paths, img_after_file]
            create_gif(gif_paths, preview_gif, duration=duration)
            downloads.append(preview_gif)

        if config.restoration_settings["create_zip"]:
            download_zip = os.path.join(output_path, output_basename + str(run_index) + ".zip")
            log.log("creating zip of frame files")
            create_zip(output_paths, download_zip)
            downloads.append(download_zip)

        if config.restoration_settings["create_txt"]:
            info_file = os.path.join(output_path, output_basename + str(run_index) + ".txt")
            create_report(info_file, img_before_file, img_after_file, num_splits, output_path, output_paths)
            downloads.append(info_file)

        return gr.Image.update(value=preview_gif), gr.File.update(value=downloads, visible=True)

def video_blender_load(project_path, frames_path1, frames_path2):
    global video_blender_state
    video_blender_state = VideoBlenderState(project_path, frames_path1, frames_path2)
    return gr.update(selected=1), 0, *video_blender_state.goto_frame(0)

def video_blender_save_project(project_name : str, project_path : str, frames1_path : str, frames2_path : str):
    global video_blender_projects
    video_blender_projects.save_project(project_name, project_path, frames1_path, frames2_path)

def video_blender_choose_project(project_name):
    global video_blender_projects
    if project_name:
        dictobj = video_blender_projects.load_project(project_name)
        if dictobj:
            return dictobj["project_name"], dictobj["project_path"], dictobj["frames1_path"], dictobj["frames2_path"]
    return #"", "", "", ""

def video_blender_prev_frame(frame : str):
    global video_blender_state
    frame = int(frame)
    frame -= 1
    return frame, *video_blender_state.goto_frame(frame)

def video_blender_next_frame(frame : str):
    global video_blender_state
    frame = int(frame)
    frame += 1
    return frame, *video_blender_state.goto_frame(frame)

def video_blender_goto_frame(frame : str):
    global video_blender_state
    frame = int(frame)
    frame = 0 if frame < 0 else frame
    return frame, *video_blender_state.goto_frame(frame)

def video_blender_skip_next(frame : str):
    global video_blender_state, config
    frame = int(frame) + int(config.blender_settings["skip_frames"])
    return frame, *video_blender_state.goto_frame(frame)

def video_blender_skip_prev(frame : str):
    global video_blender_state, config
    frame = int(frame) - int(config.blender_settings["skip_frames"])
    frame = 0 if frame < 0 else frame
    return frame, *video_blender_state.goto_frame(frame)

def video_blender_use_path1(frame : str):
    global log, video_blender_state
    frame = int(frame)
    to_filepath = video_blender_state.get_frame_file(VideoBlenderState.PROJECT_PATH, frame)
    from_filepath = video_blender_state.get_frame_file(VideoBlenderState.FRAMES1_PATH, frame)
    log.log(f"copying {from_filepath} to {to_filepath}")
    shutil.copy(from_filepath, to_filepath)
    frame += 1
    return frame, *video_blender_state.goto_frame(frame)

def video_blender_use_path2(frame : str):
    global log, video_blender_state
    frame = int(frame)
    to_filepath = video_blender_state.get_frame_file(VideoBlenderState.PROJECT_PATH, frame)
    from_filepath = video_blender_state.get_frame_file(VideoBlenderState.FRAMES2_PATH, frame)
    log.log(f"copying {from_filepath} to {to_filepath}")
    shutil.copy(from_filepath, to_filepath)
    frame += 1
    return frame, *video_blender_state.goto_frame(frame)

def video_blender_fix_frames(project_path : str, frame : float):
    return gr.update(selected=2), project_path, frame, frame

def video_blender_preview_fixed(project_path : str, before_frame : int, after_frame : int):
    global log, config, engine

    if project_path and after_frame > before_frame:
        interpolater = Interpolate(engine.model, log.log)
        target_interpolater = TargetInterpolate(interpolater, log.log)
        frame_restorer = RestoreFrames(target_interpolater, log.log)
        base_output_path = config.directories["output_blender"]
        create_directory(base_output_path)
        output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
        output_basename = "fixed_frames"

        before_file = locate_frame_file(project_path, before_frame)
        after_file = locate_frame_file(project_path, after_frame)
        num_frames = (after_frame - before_frame) - 1
        search_depth = int(config.blender_settings["frame_fixer_depth"])

        log.log(f"beginning frame fixes at {output_path}")
        frame_restorer.restore_frames(before_file, after_file, num_frames, search_depth, output_path, output_basename)
        output_paths = frame_restorer.output_paths

        preview_gif = os.path.join(output_path, output_basename + str(run_index) + ".gif")
        log.log(f"creating preview file {preview_gif}")
        duration = config.blender_settings["gif_duration"] / len(output_paths)
        gif_paths = [before_file, *output_paths, after_file]
        create_gif(gif_paths, preview_gif, duration=duration)

        return gr.Image.update(value=preview_gif), gr.Text.update(value=output_path, visible=True)

def video_blender_used_fixed(project_path : str, fixed_frames_path : str, before_frame : int):
    fixed_frames = sorted(get_files(fixed_frames_path, "png"))
    frame = before_frame + 1
    for file in fixed_frames:
        project_file = locate_frame_file(project_path, frame)
        log.log(f"copying {file} to {project_file}")
        shutil.copy(file, project_file)
        frame += 1
    return gr.update(selected=1)

def video_blender_preview_video(input_path : str):
    return gr.update(selected=3), input_path

def video_blender_render_preview(input_path : str, frame_rate : int):
    global config
    output_filepath, run_index = AutoIncrementFilename(config.directories["working"], "mp4").next_filename("video_preview", "mp4")
    ffmpeg_cmd = PNGtoMP4(input_path, "auto", int(frame_rate), output_filepath, crf=QUALITY_SMALLER_SIZE)
    return output_filepath

# def resequence_files(input_path : str, input_filetype : str, input_newname : str, input_start : str, input_step : str, input_zerofill : str, input_rename_check : bool):
    global log
    if input_path and input_filetype and input_newname and input_start and input_step and input_zerofill:
        ResequenceFiles(input_path, input_filetype, input_newname, int(input_start), int(input_step), int(input_zerofill), input_rename_check, log.log).resequence()

def convert_mp4_to_png(input_filepath : str, output_pattern : str, frame_rate : int, output_path: str):
    ffmpeg_cmd = MP4toPNG(input_filepath, output_pattern, int(frame_rate), output_path)
    return gr.update(value=ffmpeg_cmd, visible=True)

def convert_png_to_mp4(input_path : str, input_pattern : str, frame_rate : int, output_filepath: str, quality : str):
    ffmpeg_cmd = PNGtoMP4(input_path, input_pattern, int(frame_rate), output_filepath, crf=quality)
    return gr.update(value=ffmpeg_cmd, visible=True)

def convert_gif_to_mp4(input_filepath : str, output_path : str):
    ffmpeg_cmd = GIFtoPNG(input_filepath, output_path)
    return gr.update(value=ffmpeg_cmd, visible=True)

def convert_png_to_gif(input_path : str, input_pattern : str, output_filepath : str):
    ffmpeg_cmd = PNGtoGIF(input_path, input_pattern, output_filepath)
    return gr.update(value=ffmpeg_cmd, visible=True)

def convert_fc(input_path : str, output_path : str, starting_fps : int, ending_fps : int, precision : int):
    global log, config, engine
    if input_path:
        interpolater = Interpolate(engine.model, log.log)
        target_interpolater = TargetInterpolate(interpolater, log.log)
        frame_restorer = RestoreFrames(target_interpolater, log.log)
        series_upsampler = UpsampleSeries(frame_restorer, log.log)

        if output_path:
            base_output_path = output_path
        else:
            base_output_path, run_index = AutoIncrementDirectory(config.directories["output_fps_change"]).next_directory("run")

        lowest_common_rate = math.lcm(starting_fps, ending_fps)
        expansion = int(lowest_common_rate / starting_fps)
        num_frames = expansion - 1
        log.log("starting synthesis of frame superset")
        series_upsampler.upsample_series(input_path, base_output_path, num_frames, precision, f"samples@{lowest_common_rate}fps")
        frames_superset = series_upsampler.output_paths

        sample_rate = int(lowest_common_rate / ending_fps)
        sample_set = frames_superset[::sample_rate]
        log.log(f"sampled a total of {len(frames_superset)} super set frames to {len(sample_set)} {ending_fps} FPS sample frames")

        log.log(f"auto-resequencing sampled frames at {output_path}")
        ResequenceFiles(base_output_path, "png", f"resampled_frame@{ending_fps}fps", 1, 1, -1, True, log.log).resequence()

#### UI Helpers

def restart_app():
    global restart
    restart = True

def update_splits_info(num_splits : float):
    return str(max_steps(num_splits))

def update_info_fr(num_frames : int, num_splits : int):
    fractions = restored_frame_fractions(num_frames)
    predictions = restored_frame_predictions(num_frames, num_splits)
    return fractions, predictions

def update_info_fc(starting_fps : int, ending_fps : int, precision : int):
    lowest_common_rate = math.lcm(starting_fps, ending_fps)
    expansion = int(lowest_common_rate / starting_fps)
    num_frames = expansion - 1
    sample_rate = int(lowest_common_rate / ending_fps)

    filled = num_frames #if num_frames > 0 else "None"
    sampled = f"1/{sample_rate}"  #"None" if  lowest_common_rate / ending_fps

    fractions = restored_frame_fractions(num_frames) or "n/a"
    predictions = restored_frame_predictions(num_frames, precision) or "n/a"
    return lowest_common_rate, filled, sampled, fractions, predictions

def create_report(info_file : str, img_before_file : str, img_after_file : str, num_splits : int, output_path : str, output_paths : list):
    report = f"""before file: {img_before_file}
after file: {img_after_file}
number of splits: {num_splits}
output path: {output_path}
frames:
""" + "\n".join(output_paths)
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(report)

#### Gradio UI

def setup_ui(config, video_blender_projects):
    with gr.Blocks(analytics_enabled=False,
                    title="VFIformer Web UI",
                    theme=config.user_interface["theme"],
                    css=config.user_interface["css_file"]) as app:
        e = create_ui(config, video_blender_projects)

        # bind UI elemements to event handlers
        e["interpolate_button_fi"].click(frame_interpolation, inputs=[e["img1_input_fi"], e["img2_input_fi"], e["splits_input_fi"]], outputs=[e["img_output_fi"], e["file_output_fi"]])
        e["splits_input_fi"].change(update_splits_info, inputs=e["splits_input_fi"], outputs=e["info_output_fi"], show_progress=False)
        e["search_button_fs"].click(frame_search, inputs=[e["img1_input_fs"], e["img2_input_fs"], e["splits_input_fs"], e["min_input_text_fs"], e["max_input_text_fs"]], outputs=[e["img_output_fs"], e["file_output_fs"]])
        e["interpolate_button_vi"].click(video_inflation, inputs=[e["input_path_text_vi"], e["output_path_text_vi"], e["splits_input_vi"]])
        e["splits_input_vi"].change(update_splits_info, inputs=e["splits_input_vi"], outputs=e["info_output_vi"], show_progress=False)
        e["resynthesize_button_rv"].click(resynthesize_video, inputs=[e["input_path_text_rv"], e["output_path_text_rv"]])
        e["restore_button_fr"].click(frame_restoration, inputs=[e["img1_input_fr"], e["img2_input_fr"], e["frames_input_fr"], e["precision_input_fr"]], outputs=[e["img_output_fr"], e["file_output_fr"]])
        e["frames_input_fr"].change(update_info_fr, inputs=[e["frames_input_fr"], e["precision_input_fr"]], outputs=[e["times_output_fr"], e["predictions_output_fr"]], show_progress=False)
        e["precision_input_fr"].change(update_info_fr, inputs=[e["frames_input_fr"], e["precision_input_fr"]], outputs=[e["times_output_fr"], e["predictions_output_fr"]], show_progress=False)
        e["load_project_button_vb"].click(video_blender_choose_project, inputs=[e["projects_dropdown_vb"]], outputs=[e["input_project_name_vb"], e["input_project_path_vb"], e["input_path1_vb"], e["input_path2_vb"]], show_progress=False)
        e["save_project_button_vb"].click(video_blender_save_project, inputs=[e["input_project_name_vb"], e["input_project_path_vb"], e["input_path1_vb"], e["input_path2_vb"]], show_progress=False)
        e["load_button_vb"].click(video_blender_load, inputs=[e["input_project_path_vb"], e["input_path1_vb"], e["input_path2_vb"]], outputs=[e["tabs_video_blender"], e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["prev_frame_button_vb"].click(video_blender_prev_frame, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["next_frame_button_vb"].click(video_blender_next_frame, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["go_button_vb"].click(video_blender_goto_frame, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["input_text_frame_vb"].submit(video_blender_goto_frame, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["use_path_1_button_vb"].click(video_blender_use_path1, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["use_path_2_button_vb"].click(video_blender_use_path2, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["prev_xframes_button_vb"].click(video_blender_skip_prev, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["next_xframes_button_vb"].click(video_blender_skip_next, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["preview_video_vb"].click(video_blender_preview_video, inputs=e["input_project_path_vb"], outputs=[e["tabs_video_blender"], e["preview_path_vb"]])
        e["fix_frames_button_vb"].click(video_blender_fix_frames, inputs=[e["input_project_path_vb"], e["input_text_frame_vb"]], outputs=[e["tabs_video_blender"], e["project_path_ff"], e["input_clean_before_ff"], e["input_clean_after_ff"]])
        e["preview_button_ff"].click(video_blender_preview_fixed, inputs=[e["project_path_ff"], e["input_clean_before_ff"], e["input_clean_after_ff"]], outputs=[e["preview_image_ff"], e["fixed_path_ff"]])
        e["use_fixed_button_ff"].click(video_blender_used_fixed, inputs=[e["project_path_ff"], e["fixed_path_ff"], e["input_clean_before_ff"]], outputs=e["tabs_video_blender"])
        e["render_video_vb"].click(video_blender_render_preview, inputs=[e["preview_path_vb"], e["input_frame_rate_vb"]], outputs=[e["video_preview_vb"]])
        e["convert_button_mp"].click(convert_mp4_to_png, inputs=[e["input_path_text_mp"], e["output_pattern_text_mp"], e["input_frame_rate_mp"], e["output_path_text_mp"]], outputs=e["output_info_text_mp"])
        e["convert_button_pm"].click(convert_png_to_mp4, inputs=[e["input_path_text_pm"], e["input_pattern_text_pm"], e["input_frame_rate_pm"], e["output_path_text_pm"], e["quality_slider_pm"]], outputs=e["output_info_text_pm"])
        e["convert_button_gp"].click(convert_gif_to_mp4, inputs=[e["input_path_text_gp"], e["output_path_text_gp"]], outputs=e["output_info_text_gp"])
        e["convert_button_pg"].click(convert_png_to_gif, inputs=[e["input_path_text_pg"], e["input_pattern_text_pg"], e["output_path_text_pg"]], outputs=e["output_info_text_pg"])
        e["resequence_button"].click(resequence_files, inputs=[e["input_path_text2"], e["input_filetype_text"], e["input_newname_text"], e["input_start_text"], e["input_step_text"], e["input_zerofill_text"], e["input_rename_check"]])
        e["restart_button"].click(restart_app, _js="function(){setTimeout(function(){window.location.reload()},2000);return[]}")
        e["starting_fps_fc"].change(update_info_fc, inputs=[e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]], outputs=[e["output_lcm_text_fc"], e["output_filler_text_fc"], e["output_sampled_text_fc"], e["times_output_fc"], e["predictions_output_fc"]], show_progress=False)
        e["ending_fps_fc"].change(update_info_fc, inputs=[e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]], outputs=[e["output_lcm_text_fc"], e["output_filler_text_fc"], e["output_sampled_text_fc"], e["times_output_fc"], e["predictions_output_fc"]], show_progress=False)
        e["precision_fc"].change(update_info_fc, inputs=[e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]], outputs=[e["output_lcm_text_fc"], e["output_filler_text_fc"], e["output_sampled_text_fc"], e["times_output_fc"], e["predictions_output_fc"]], show_progress=False)
        e["convert_button_fc"].click(convert_fc, inputs=[e["input_path_text_fc"], e["output_path_text_fc"], e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]])

    return app

# _js="function(){alert(\"Project Saved!\r\n\r\nReload application from the Tools page to see it in the dropdown list.\");return[]}"

#### code borrowed from stable-diffusion-webui webui.py:
def wait_on_server(app):
    global restart
    while True:
        time.sleep(0.5)
        if restart:
            restart = False
            time.sleep(0.5)
            app.close()
            time.sleep(0.5)
            break

# make the program just exit at ctrl+c without waiting for anything
def sigint_handler(sig, frame):
    print(f'Interrupted with signal {sig} in {frame}')
    os._exit(0)

signal.signal(signal.SIGINT, sigint_handler)

if __name__ == '__main__':
    main()
