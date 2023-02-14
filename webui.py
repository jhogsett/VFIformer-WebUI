import os
import shutil
import time
import signal
import argparse
import csv
import gradio as gr
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from deep_interpolate import DeepInterpolate
from interpolate_series import InterpolateSeries
from webui_utils.simple_log import SimpleLog
from webui_utils.simple_config import SimpleConfig
from webui_utils.auto_increment import AutoIncrementDirectory, AutoIncrementFilename
from webui_utils.image_utils import create_gif
from webui_utils.file_utils import create_directories, create_zip, get_files, create_directory
from webui_utils.simple_utils import max_steps, restored_frame_fractions, restored_frame_predictions
from webui_utils.video_utils import MP4toPNG, PNGtoMP4, QUALITY_SMALLER_SIZE
from resequence_files import ResequenceFiles
from interpolation_target import TargetInterpolate
from restore_frames import RestoreFrames

log = None
config = None
engine= None
restart = False
prevent_inbrowser = False
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
        app = create_ui()
        app.launch(inbrowser = config.auto_launch_browser and not prevent_inbrowser,
                    server_name = config.server_name,
                    server_port = config.server_port,
                    prevent_thread_lock=True)

        # idea borrowed from stable-diffusion-webui webui.py
        # after initial launch, disable inbrowser for subsequent restarts
        prevent_inbrowser = True

        wait_on_server(app)
        print("Restarting...")

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

class VideoBlenderPath:
    def __init__(self, path : str):
        self.path = path
        self.files = sorted(os.listdir(self.path))
        self.last_frame = len(self.files) - 1
        self.load_file_info()

    def load_file_info(self):
        files = sorted(os.listdir(self.path))
        self.files = [os.path.join(self.path, file) for file in files]
        self.file_count = len(self.files)

    def get_frame(self, frame : int):
        if frame < 0 or frame > self.last_frame:
            return None
        else:
            return self.files[frame]

class VideoBlenderProjects:
    FIELDS = ["project_name", "project_path", "frames1_path", "frames2_path"]

    def __init__(self, csvfile_path):
        self.csvfile_path = csvfile_path
        self.projects = {}
        self.read_projects()

    def read_projects(self):
        if os.path.isfile(self.csvfile_path):
            reader = csv.DictReader(open(self.csvfile_path))
            entries = list(reader)
            for entry in entries:
                project_name = entry["project_name"]
                self.projects[project_name] = entry

    def write_projects(self):
        project_names = self.get_project_names()
        row_array = [self.projects[project_name] for project_name in project_names]
        with open(self.csvfile_path, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames = self.FIELDS)
            writer.writeheader()
            writer.writerows(row_array)

    def get_project_names(self):
        return list(self.projects.keys())

    def load_project(self, project_name : str):
        return self.projects[project_name]

    def save_project(self, project_name : str, project_path : str, frames1_path : str, frames2_path : str):
        self.projects[project_name] = {
            "project_name" : project_name,
            "project_path" : project_path,
            "frames1_path" : frames1_path,
            "frames2_path" : frames2_path
        }
        self.write_projects()

class VideoBlenderState:
    # which_path index into the path info list
    PROJECT_PATH = 0
    FRAMES1_PATH = 1
    FRAMES2_PATH = 2

    def __init__(self, project_path : str, frames_path1 : str, frames_path2 : str):
        self.project_path = project_path
        self.frames_path1 = frames_path1
        self.frames_path2 = frames_path2
        self.current_frame = 0
        self.path_info = [
            VideoBlenderPath(project_path),
            VideoBlenderPath(frames_path1),
            VideoBlenderPath(frames_path2)
            ]

    def get_frame_file(self, which_path : int, frame : int):
        return self.path_info[which_path].get_frame(frame)

    def get_frame_files(self, frame : int):
        results = []
        results.append(self.get_frame_file(self.FRAMES1_PATH, frame))
        results.append(self.get_frame_file(self.PROJECT_PATH, frame - 1))
        results.append(self.get_frame_file(self.PROJECT_PATH, frame))
        results.append(self.get_frame_file(self.PROJECT_PATH, frame + 1))
        results.append(self.get_frame_file(self.FRAMES2_PATH, frame))
        return results

    def goto_frame(self, frame : int):
        self.current_frame = frame
        return self.get_frame_files(frame)

global video_blender_state
video_blender_state = None

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

def video_blender_preview_video(input_path : str):
    return gr.update(selected=2), input_path

def video_blender_render_preview(input_path : str, frame_rate : int):
    global config
    output_filepath, run_index = AutoIncrementFilename(config.directories["working"], "mp4").next_filename("video_preview", "mp4")
    ffmpeg_cmd = PNGtoMP4(input_path, "auto", int(frame_rate), output_filepath, crf=QUALITY_SMALLER_SIZE)
    return output_filepath

def resequence_files(input_path : str, input_filetype : str, input_newname : str, input_start : str, input_step : str, input_zerofill : str, input_rename_check : bool):
    global log
    if input_path and input_filetype and input_newname and input_start and input_step and input_zerofill:
        ResequenceFiles(input_path, input_filetype, input_newname, int(input_start), int(input_step), int(input_zerofill), input_rename_check, log.log).resequence()

def convert_mp4_to_png(input_filepath : str, output_pattern : str, frame_rate : int, output_path: str):
    ffmpeg_cmd = MP4toPNG(input_filepath, output_pattern, int(frame_rate), output_path)
    return gr.update(value=ffmpeg_cmd, visible=True)

def convert_png_to_mp4(input_path : str, input_pattern : str, frame_rate : int, output_filepath: str, quality : str):
    ffmpeg_cmd = PNGtoMP4(input_path, input_pattern, int(frame_rate), output_filepath, crf=quality)
    return gr.update(value=ffmpeg_cmd, visible=True)

def restart_app():
    global restart
    restart = True

def update_splits_info(num_splits : float):
    return str(max_steps(num_splits))

def update_info_fr(num_frames : int, num_splits : int):
    fractions = restored_frame_fractions(num_frames)
    predictions = restored_frame_predictions(num_frames, num_splits)
    return fractions, predictions

#### UI Helpers

def create_report(info_file : str, img_before_file : str, img_after_file : str, num_splits : int, output_path : str, output_paths : list):
    report = f"""before file: {img_before_file}
after file: {img_after_file}
number of splits: {num_splits}
output path: {output_path}
frames:
""" + "\n".join(output_paths)
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(report)

#### Create Gradio UI

def create_ui():
    global config, video_blender_projects
    with gr.Blocks(analytics_enabled=False,
                    title="VFIformer Web UI",
                    theme=config.user_interface["theme"],
                    css=config.user_interface["css_file"]) as app:
        gr.HTML("VFIformer Web UI", elem_id="appheading")

        with gr.Tab("Frame Interpolation"):
            gr.HTML("Divide the time between two frames to any depth, see an animation of result and download the new frames", elem_id="tabheading")
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    img1_input_fi = gr.Image(type="filepath", label="Before Image", tool=None)
                    img2_input_fi = gr.Image(type="filepath", label="After Image", tool=None)
                    with gr.Row(variant="compact"):
                        splits_input_fi = gr.Slider(value=1, minimum=1, maximum=config.interpolation_settings["max_splits"], step=1, label="Splits")
                        info_output_fi = gr.Textbox(value="1", label="Interpolated Frames", max_lines=1, interactive=False)
                with gr.Column(variant="panel"):
                    img_output_fi = gr.Image(type="filepath", label="Animated Preview", interactive=False)
                    file_output_fi = gr.File(type="file", file_count="multiple", label="Download", visible=False)
            interpolate_button_fi = gr.Button("Interpolate", variant="primary")
            with gr.Accordion("Tips", open=False):
                gr.Markdown("""
                - Use this tool to reveal intricate details of the motion occurring between two video frames
                - Use it to quickly recreate a damaged frame
                  - Set split count to _1_ and provide the _adjacent frames_
                  - The _Frame Restoration_ tool can be used to recreate an arbitrary number of adjacent frames
                """)

        with gr.Tab("Frame Search"):
            gr.HTML("Search for an arbitrarily precise timed frame and return the closest match", elem_id="tabheading")
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    img1_input_fs = gr.Image(type="filepath", label="Before Image", tool=None)
                    img2_input_fs = gr.Image(type="filepath", label="After Image", tool=None)
                    with gr.Row(variant="compact"):
                        splits_input_fs = gr.Slider(value=1, minimum=1, maximum=config.search_settings["max_splits"], step=1, label="Search Depth")
                        min_input_text_fs = gr.Text(placeholder="0.0-1.0", label="Lower Bound")
                        max_input_text_fs = gr.Text(placeholder="0.0-1.0", label="Upper Bound")
                with gr.Column(variant="panel"):
                    img_output_fs = gr.Image(type="filepath", label="Found Frame", interactive=False)
                    file_output_fs = gr.File(type="file", file_count="multiple", label="Download", visible=False)
            search_button_fs = gr.Button("Search", variant="primary")
            with gr.Accordion("Tips", open=False):
                gr.Markdown("""
                - Use this tool to synthesize a frame at an arbitrarily precise time using _Targeted Interpolation_
                  - This is similar to a binary search:
                    - The time interval between two frames is _halved_ recursively in the direction of the search target
                    - New _between frames_ are interpolated at each step
                    - A match is returned when a frame is found inside the search window, or if the search depth is reached
                  - Search Depth should be set high if a precisely timed frame is needed
                    - A low search depth may match a frame outside the search window""")

        with gr.Tab("Video Inflation"):
            gr.HTML("Double the number of video frames to any depth for super slow motion", elem_id="tabheading")
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    input_path_text_vi = gr.Text(max_lines=1, placeholder="Path on this server to the frame PNG files", label="Input Path")
                    output_path_text_vi = gr.Text(max_lines=1, placeholder="Where to place the generated frames, leave blank to use default", label="Output Path")
                    with gr.Row(variant="compact"):
                        splits_input_vi = gr.Slider(value=1, minimum=1, maximum=10, step=1, label="Splits")
                        info_output_vi = gr.Textbox(value="1", label="Interpolations per Frame", max_lines=1, interactive=False)
            gr.Markdown("*Progress can be tracked in the console*")
            interpolate_button_vi = gr.Button("Interpolate Series (this will take time)", variant="primary")
            with gr.Accordion("Tips", open=False):
                gr.Markdown("""
                - This tool uses _Frame Interpolation_ on a sequence of video frame PNG files to double the frame count any number of times
                - This can have useful purposes:
                  - Turn a regular video into a _super-slow-motion_ video
                  - Expand the frames in a _time lapse_ video to _recover the original real-time video_
                  - Create _smooth motion_ from otherwise _discrete motion_, like the second hand of a ticking clock

                # Important
                - This process will be slow, perhaps many hours long!
                - Progress will be shown in the console using a standard tqdm progress bar
                - The browser can be safely closed without interupting the process
                - There currently isn't an easy way to resume a halted inflation
                  - A possible workaround:
                    - Set aside the already-rendered frames from the input path
                    - Re-run the inflation
                    - Use the _Resequence Files_ tool to remix the two sets of rendered frames""")

        with gr.Tab("Resynthesize Video"):
            gr.HTML("Interpolate replacement frames from an entire video for use in movie restoration", elem_id="tabheading")
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    input_path_text_rv = gr.Text(max_lines=1, placeholder="Path on this server to the frame PNG files", label="Input Path")
                    output_path_text_rv = gr.Text(max_lines=1, placeholder="Where to place the generated frames, leave blank to use default", label="Output Path")
            gr.Markdown("*Progress can be tracked in the console*")
            resynthesize_button_rv = gr.Button("Resynthesize Video (this will take time)", variant="primary")
            with gr.Accordion("Tips", open=False):
                gr.Markdown("""
                - This tool creates a set of replacement frames for a video by interpolating new frames between all existing frames
                  - For each replacement frame, the two adjacent original frames are used to interpolate a new _replacement frame_
                    - Example:
                      - create a new frame #1 by interpolating a _between frame_ using original frames #0 and #2
                      - then create a new frame #2 using original frames #1 and #3
                      - then repeat this process for all frames in the original video
                    - When done, there will be a complete set of synthesized replacement frames, matching frames in the original video, that can be used for movie restoration
                      - The _first_ and _last_ original frames cannot be resynthesized
                - How to use the replacement frames
                  - The _Video Blender_ tool can be used to manually step through a video, easily replacing frames from a restoration set
                - Why this works
                  - A video may have a single bad frame between two good frames
                    - For example a bad splice, a video glitch, a double-exposed frame due to a mismatch in frame rates, etc.
                  - VFIformer is excellent at detecting motion in all parts of a pair of frames, and will very accurately create a new clean replacement frame
                - When it doesn't work
                  - It will not work to create replacement frames when there are not two adjacent CLEAN original frames
                    - The _Frame Restoration_ tool can be used to recover an arbitrary number of adjacent damaged frames
                  - It will not work to clean up transitions between scenes
                  - If the motion between the two frames is too quick, it may not be detectable
                    - Examples:
                      - An ax chopping wood may have moved too fast for any motion to be captured by the camera
                      - A first-person POV of a rollercoaster ride may have motion that's too different between frames to be detectable""")

        with gr.Tab("Frame Restoration"):
            gr.HTML("Restore multiple adjacent bad frames using precision interpolation", elem_id="tabheading")
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    with gr.Row(variant="compact"):
                        img1_input_fr = gr.Image(type="filepath", label="Frame Before Replacement Frames", tool=None)
                        img2_input_fr = gr.Image(type="filepath", label="Frame After Replacement Frames", tool=None)
                    with gr.Row(variant="compact"):
                        frames_input_fr = gr.Slider(value=config.restoration_settings["default_frames"], minimum=1, maximum=config.restoration_settings["max_frames"], step=1, label="Frames to Restore")
                        precision_input_fr = gr.Slider(value=config.restoration_settings["default_precision"], minimum=1, maximum=config.restoration_settings["max_precision"], step=1, label="Search Precision")
                    with gr.Row(variant="compact"):
                        times_default = restored_frame_fractions(config.restoration_settings["default_frames"])
                        times_output_fr = gr.Textbox(value=times_default, label="Frame Search Times", max_lines=1, interactive=False)
                with gr.Column(variant="panel"):
                    img_output_fr = gr.Image(type="filepath", label="Animated Preview", interactive=False)
                    file_output_fr = gr.File(type="file", file_count="multiple", label="Download", visible=False)
            predictions_default = restored_frame_predictions(config.restoration_settings["default_frames"], config.restoration_settings["default_precision"])
            predictions_output_fr = gr.Textbox(value=predictions_default, label="Predicted Matches", max_lines=1, interactive=False)
            restore_button_fr = gr.Button("Restore Frames", variant="primary")
            with gr.Accordion("Tips", open=False):
                gr.Markdown("""
                - This tool uses _Frame Search_ to create restored frames for a series of adjacent bad frames
                - It can be used when basic _Frame Interpolation_ cannot due to the lack of adjacent clean frames
                - _Targeted Interpolation_ is used to search for replacement frames at precise times between the outer clean frames

                # Important
                - Provide only CLEAN frames adjacent to the series of bad frames
                  - The frames should not cross scenes
                  - Motion that is too fast may not produce good results
                - Set _Frames to Restore_ to the exact number of bad frames that need replacing to get accurate results
                - _Frame Search Times_ shows the fractional search times for the restored frames
                  - Example with four frames:
                    - If there are 2 bad frames b and c, and 2 good frames A and D:
                      - A---b---c---D
                      - Replacement frame B is 1/3 of the way between frames A and D
                      - Replacement frame C is 2/3 of the way between frames A and D
                      - _Targeted Interpolation_ can recreate frames at these precise times
                - Set _Search Precision_ to the _search depth_ needed for accuracy
                  - Low _Search Precision_ is faster but can lead to repeated or poorly-timed frames
                  - High _Search Precision_ takes longer but can produce near-perfect results
                    - When restoring an even number of frames
                    - When extreme accuracy is the goal
                - _Predicted Matches_ estimates the frame times that will be found based on _Frames to Restore_ and _Search Precision_
                  - The actual found frames may differ from the predictions
                  - A warning is displayed if _Search Precision_ should be increased because of possible repeated frames""")

        with gr.Tab("Video Blender"):
            gr.HTML("Combine original and replacement frames to manually restore a video", elem_id="tabheading")
            tabs_video_blender = gr.Tabs()
            with tabs_video_blender:
                with gr.Tab("Project Settings", id=0):
                    with gr.Row():
                        input_project_name_vb = gr.Textbox(label="Project Name")
                        projects_dropdown_vb = gr.Dropdown(label="Saved Project Settings", choices=video_blender_projects.get_project_names())
                        load_project_button_vb = gr.Button("Load").style(full_width=False)
                        save_project_button_vb = gr.Button("Save").style(full_width=False)
                    with gr.Row():
                        input_project_path_vb = gr.Textbox(label="Project Frames Path", placeholder="Path to frame PNG files for video being restored")
                    with gr.Row():
                        input_path1_vb = gr.Textbox(label="Original / Video #1 Frames Path", placeholder="Path to original or video #1 PNG files")
                    with gr.Row():
                        input_path2_vb = gr.Textbox(label="Alternate / Video #2 Frames Path", placeholder="Path to alternate or video #2 PNG files")
                    load_button_vb = gr.Button("Open Video Blender Project", variant="primary")
                    with gr.Accordion("Tips", open=False):
                        gr.Markdown("""
                        - Set up the project with three directories, all with PNG files (only) with the _same file count, dimensions and starting sequence number_
                        - The _Original / Video #1 Frames Path_ should have the _original PNG files_ from the video being restored
                        - The _Project Frames Path_ should start with a _copy of the original PNG files_ as a baseline set of frames
                        - The _Alternate / Video #2 Frames Path_ directory should have a set of _replacement PNG files_ used for restoration
                          - Replacement frames can be created using the _Resynthesize Video_ feature

                        # Important
                        - All paths must have the same number of files with _corresponding sequence numbers and dimensions_
                          - The _Resequence Files_ tool can be used to rename a set of PNG files
                        - For _Video Preview_ to work properly:
                          - The files in each directory must have the _same base filename and numbering sequence_
                          - `ffmpeg.exe` must be available on the _system path_ to convert PNG frames for the preview video

                        # Project Management
                        - To save a settings for a project:
                          - After filling out all project text boxes, click _Save_
                          - A new row will be added to the projects file `./video_blender_projects.csv`
                          - To see the new project in the dropdown list:
                            - Restart the application via the Tools page, or from the console
                            - Reload the browser page and go back to the _Video Blender_ tab
                        - To load settings for a project
                          - Choose a project by name from the_Saved Project Settings_ DropDown
                          - Click _Load_
                          - Click _Open Video Blender Project_ to load the project and go to the _Frame Chooser_

                        General Use
                        - This tool can also be used any time there's a need to mix three videos, selectively replacing frames in one with frames from two others""")

                with gr.Tab("Frame Chooser", id=1):
                    with gr.Row():
                        with gr.Column():
                            gr.Textbox(visible=False)
                        with gr.Column():
                            output_img_path1_vb = gr.Image(label="Original / Path 1 Frame", interactive=False, type="filepath")
                        with gr.Column():
                            gr.Textbox(visible=False)
                    with gr.Row():
                        with gr.Column():
                            output_prev_frame_vb = gr.Image(label="Previous Frame", interactive=False, type="filepath", elem_id="sideimage")
                        with gr.Column():
                            output_curr_frame_vb = gr.Image(label="Current Frame", interactive=False, type="filepath")
                        with gr.Column():
                            output_next_frame_vb = gr.Image(label="Next Frame", interactive=False, type="filepath", elem_id="sideimage")
                    with gr.Row():
                        with gr.Column():
                            with gr.Row():
                                prev_frame_button_vb = gr.Button("< Prev Frame")
                                next_frame_button_vb = gr.Button("Next Frame >")
                            with gr.Row():
                                go_button_vb = gr.Button("Go").style(full_width=False)
                                # TODO change this to a gr.Number()
                                input_text_frame_vb = gr.Textbox(value="0", label="Frame")
                            with gr.Row():
                                # TODO mention in the buttons the number of skipped frames
                                prev_xframes_button_vb = gr.Button(f"<< {config.blender_settings['skip_frames']}")
                                next_xframes_button_vb = gr.Button(f"{config.blender_settings['skip_frames']} >>")
                        with gr.Column():
                            output_img_path2_vb = gr.Image(label="Repair / Path 2 Frame", interactive=False, type="filepath")
                        with gr.Column():
                            use_path_1_button_vb = gr.Button("Use Path 1 Frame | Next >", variant="primary")
                            use_path_2_button_vb = gr.Button("Use Path 2 Frame | Next >", variant="primary")
                            use_back_button_vb = gr.Button("< Back")
                            preview_video_vb = gr.Button("Preview Video")
                    with gr.Accordion("Tips", open=False):
                        gr.Markdown("""
                        # Important
                        - The orange buttons copy files!
                          - They copy the corresponding frame PNG file from their respective directories to the project path
                          - The existing frame PNG file in the project path is overwritten
                          - The gray buttons can be used without altering the project

                        Use the _Next Frame_ and _Prev Frame_ buttons to step through the video one frame at a time
                          - Tip: Press _Tab_ until the _Next Frame_ button is in focus, then use the SPACEBAR to step through the video

                        Clicking _Preview Video_ will take you to the _Preview Video_ tab
                          - The current set of project PNG frame files can be rendered into a video and watched""")

                with gr.Tab("Video Preview", id=2):
                    with gr.Row():
                        video_preview_vb = gr.Video(label="Preview", interactive=False, include_audio=False) #.style(width=config.blender_settings["preview_width"]) #height=config.blender_settings["preview_height"],
                    preview_path_vb = gr.Textbox(max_lines=1, label="Path to PNG Sequence", placeholder="Path on this server to the PNG files to be converted")
                    with gr.Row():
                        render_video_vb = gr.Button("Render Video", variant="primary")
                        input_frame_rate_vb = gr.Slider(minimum=1, maximum=60, value=config.png_to_mp4_settings["frame_rate"], step=1, label="Frame Rate")
                    with gr.Accordion("Tips", open=False):
                        gr.Markdown("""
                        - When coming to this tab from the _Frame Choose_ tab's _Preview Video_ button, the _Path to PNG Sequence_ is automatically filled with the Video Blender project path
                          - Simply click _Render Video_ to create and watch a preview of the project in its current state
                        - Preview videos are rendered in the directory set by the `directories:working` variable in `config.yaml`
                          - The directory is `./temp` by default and is not automatically purged

                        # Tip
                        - This tab can be used to render and watch a preview video for any directory of video frame PNG files
                        - Requirements:
                          - The files must be video frame PNG files with the same dimensions
                          - The filenames must all confirm to the same requirements:
                            - Have the same starting base filename
                            - Followed by a frame index integer, all zero-filled to the same width
                            - Example: `FRAME001.png` through `FRAME420.png`
                          - There must be no other PNG files in the same directory""")

        with gr.Tab("Tools"):
            with gr.Row(variant="compact"):
                restart_button = gr.Button("Restart App", variant="primary").style(full_width=False)

            with gr.Tab("Resequence Files"):
                gr.HTML("Rename a PNG sequence for import into video editing software", elem_id="tabheading")
                with gr.Row(variant="compact"):
                    with gr.Column(variant="panel"):
                        input_path_text2 = gr.Text(max_lines=1, placeholder="Path on this server to the files to be resequenced", label="Input Path")
                        with gr.Row(variant="compact"):
                            input_filetype_text = gr.Text(value="png", max_lines=1, placeholder="File type such as png", label="File Type")
                            input_newname_text = gr.Text(value="pngsequence", max_lines=1, placeholder="Base filename for the resequenced files", label="Base Filename")
                        with gr.Row(variant="compact"):
                            input_start_text = gr.Text(value="0", max_lines=1, placeholder="Starting integer for the sequence", label="Starting Sequence Number")
                            input_step_text = gr.Text(value="1", max_lines=1, placeholder="Integer tep for the sequentially numbered files", label="Integer Step")
                            input_zerofill_text = gr.Text(value="-1", max_lines=1, placeholder="Padding with for sequential numbers, -1=auto", label="Number Padding")
                        with gr.Row(variant="compact"):
                            input_rename_check = gr.Checkbox(value=False, label="Rename instead of duplicate files")
                        resequence_button = gr.Button("Resequence Files", variant="primary")
                with gr.Accordion("Tips", open=False):
                    gr.Markdown("""
                    - The only PNG files present in the _Input Path_ should be the video frame files
                    - _File Type_ is used for a wildcard search of files
                    - _Base Filename_ is used to name the resequenced files with an added frame number
                    - _Starting Sequence Number_ normally should be _0_
                        - A different value might be useful if inserting a PNG sequence into another
                    - _Integer Step_ normally should be _1_
                        - This sets the increment between the added frame numbers
                    - _Number Padding_ should be _-1_ for automatic detection
                        - It can be set to another value if a specific width of digits is needed for the frame number
                    - Leave _Rename instead of duplicate files_ unchecked if the original files might be needed
                      - This can be helpful for tracing back to the source frame""")

            with gr.Tab("File Conversion"):
                gr.HTML("Tools for common video file conversion tasks (ffmpeg.exe must be in path)", elem_id="tabheading")

                with gr.Tab("MP4 to PNG Sequence"):
                    gr.Markdown("Convert MP4 to a PNG sequence")
                    input_path_text_mp = gr.Text(max_lines=1, label="MP4 File", placeholder="Path on this server to the MP4 file to be converted")
                    output_path_text_mp = gr.Text(max_lines=1, label="PNG Files Path", placeholder="Path on this server to a directory for the converted PNG files")
                    with gr.Row():
                        output_pattern_text_mp = gr.Text(max_lines=1, label="Output Filename Pattern", placeholder="Pattern like image%03d.png")
                        input_frame_rate_mp = gr.Slider(minimum=1, maximum=60, value=config.mp4_to_png_settings["frame_rate"], step=1, label="Frame Rate")
                    convert_button_mp = gr.Button("Convert", variant="primary")
                    output_info_text_mp = gr.Textbox(label="Details", interactive=False)
                    with gr.Accordion("Tips", open=False):
                        gr.Markdown("""
                        - The filename pattern should be based on the count of frames  for alphanumeric sorting
                        - Example: For a video with _24,578_ frames and a PNG base filename of "TENNIS", the pattern should be "TENNIS%05d.png"
                        - Match the frame rate to the rate of the source video to avoid repeated or skipped frames
                        - The _Video Preview_ tab on the _Video Blender_ page can be used to watch a preview video of a set of PNG files""")

                with gr.Tab("PNG Sequence to MP4"):
                    gr.Markdown("Convert a PNG sequence to a MP4")
                    input_path_text_pm = gr.Text(max_lines=1, label="PNG Files Path", placeholder="Path on this server to the PNG files to be converted")
                    output_path_text_pm = gr.Text(max_lines=1, label="MP4 File", placeholder="Path and filename on this server for the converted MP4 file")
                    with gr.Row():
                        input_pattern_text_pm = gr.Text(max_lines=1, label="Input Filename Pattern", placeholder="Pattern like image%03d.png (auto=automatic pattern)")
                        input_frame_rate_pm = gr.Slider(minimum=1, maximum=60, value=config.png_to_mp4_settings["frame_rate"], step=1, label="Frame Rate")
                        quality_slider_pm = gr.Slider(minimum=config.png_to_mp4_settings["minimum_crf"], maximum=config.png_to_mp4_settings["maximum_crf"], step=1, value=config.png_to_mp4_settings["default_crf"], label="Quality (lower=better)")
                    convert_button_pm = gr.Button("Convert", variant="primary")
                    output_info_text_pm = gr.Textbox(label="Details", interactive=False)
                    with gr.Accordion("Tips", open=False):
                        gr.Markdown("""
                        - The filename pattern should be based on the number of PNG files to ensure they're read in alphanumeric order
                        - Example: For a PNG sequence with _24,578_ files and filenames like "TENNIS24577.png", the pattern should be "TENNIS%05d.png"
                        - The special pattern "auto" can be used to detect the pattern automatically. This works when:
                            - The only PNG files present are the frame images
                            - All files have the same naming pattern, starting with a base filename, and the same width zero-filled frame number
                            - The first found PNG file follows the same naming pattern as all the other files
                        - The _Video Preview_ tab on the _Video Blender_ page can be used to watch a preview video of a set of PNG files""")

                with gr.Tab("GIF to PNG Sequence*"):
                    gr.Markdown("*Planned: Convert a GIF to a PNG sequence")

                with gr.Tab("PNG Sequence to GIF*"):
                    gr.Markdown("*Planned: Convert a PNG sequence to a GIF, specify duration and looping")

            with gr.Tab("Upscaling*"):
                gr.Markdown("*Planned: Use Real-ESRGAN 4x+ to restore and/or upscale images")

            with gr.Tab("GIF to Video*"):
                with gr.Row(variant="compact"):
                    with gr.Column(variant="panel"):
                        gr.Markdown("""
                        *Idea: Recover the original video from animated GIF file
                        - split GIF into a series of PNG frames
                        - use R-ESRGAN 4x+ to restore and/or upscale
                        - use VFIformer to adjust frame rate to real time
                        - reassemble new PNG frames into MP4 file""")

        interpolate_button_fi.click(frame_interpolation, inputs=[img1_input_fi, img2_input_fi, splits_input_fi], outputs=[img_output_fi, file_output_fi])
        splits_input_fi.change(update_splits_info, inputs=splits_input_fi, outputs=info_output_fi, show_progress=False)

        search_button_fs.click(frame_search, inputs=[img1_input_fs, img2_input_fs, splits_input_fs, min_input_text_fs, max_input_text_fs], outputs=[img_output_fs, file_output_fs])

        interpolate_button_vi.click(video_inflation, inputs=[input_path_text_vi, output_path_text_vi, splits_input_vi])
        splits_input_vi.change(update_splits_info, inputs=splits_input_vi, outputs=info_output_vi, show_progress=False)

        resynthesize_button_rv.click(resynthesize_video, inputs=[input_path_text_rv, output_path_text_rv])

        restart_button.click(restart_app) #, _js="setTimeout(function(){location.reload()},2000)")

        resequence_button.click(resequence_files, inputs=[input_path_text2, input_filetype_text, input_newname_text, input_start_text, input_step_text, input_zerofill_text, input_rename_check])

        convert_button_mp.click(convert_mp4_to_png, inputs=[input_path_text_mp, output_pattern_text_mp, input_frame_rate_mp, output_path_text_mp], outputs=output_info_text_mp)
        convert_button_pm.click(convert_png_to_mp4, inputs=[input_path_text_pm, input_pattern_text_pm, input_frame_rate_pm, output_path_text_pm, quality_slider_pm], outputs=output_info_text_pm)

        restore_button_fr.click(frame_restoration, inputs=[img1_input_fr, img2_input_fr, frames_input_fr, precision_input_fr], outputs=[img_output_fr, file_output_fr])
        frames_input_fr.change(update_info_fr, inputs=[frames_input_fr, precision_input_fr], outputs=[times_output_fr, predictions_output_fr], show_progress=False)
        precision_input_fr.change(update_info_fr, inputs=[frames_input_fr, precision_input_fr], outputs=[times_output_fr, predictions_output_fr], show_progress=False)

        load_project_button_vb.click(video_blender_choose_project, inputs=[projects_dropdown_vb], outputs=[input_project_name_vb, input_project_path_vb, input_path1_vb, input_path2_vb], show_progress=False)
        save_project_button_vb.click(video_blender_save_project, inputs=[input_project_name_vb, input_project_path_vb, input_path1_vb, input_path2_vb], show_progress=False)
        load_button_vb.click(video_blender_load, inputs=[input_project_path_vb, input_path1_vb, input_path2_vb], outputs=[tabs_video_blender, input_text_frame_vb, output_img_path1_vb, output_prev_frame_vb, output_curr_frame_vb, output_next_frame_vb, output_img_path2_vb], show_progress=False)

        prev_frame_button_vb.click(video_blender_prev_frame, inputs=[input_text_frame_vb], outputs=[input_text_frame_vb, output_img_path1_vb, output_prev_frame_vb, output_curr_frame_vb, output_next_frame_vb, output_img_path2_vb], show_progress=False)
        next_frame_button_vb.click(video_blender_next_frame, inputs=[input_text_frame_vb], outputs=[input_text_frame_vb, output_img_path1_vb, output_prev_frame_vb, output_curr_frame_vb, output_next_frame_vb, output_img_path2_vb], show_progress=False)
        go_button_vb.click(video_blender_goto_frame, inputs=[input_text_frame_vb], outputs=[input_text_frame_vb, output_img_path1_vb, output_prev_frame_vb, output_curr_frame_vb, output_next_frame_vb, output_img_path2_vb], show_progress=False)
        input_text_frame_vb.submit(video_blender_goto_frame, inputs=[input_text_frame_vb], outputs=[input_text_frame_vb, output_img_path1_vb, output_prev_frame_vb, output_curr_frame_vb, output_next_frame_vb, output_img_path2_vb], show_progress=False)
        use_path_1_button_vb.click(video_blender_use_path1, inputs=[input_text_frame_vb], outputs=[input_text_frame_vb, output_img_path1_vb, output_prev_frame_vb, output_curr_frame_vb, output_next_frame_vb, output_img_path2_vb], show_progress=False)
        use_path_2_button_vb.click(video_blender_use_path2, inputs=[input_text_frame_vb], outputs=[input_text_frame_vb, output_img_path1_vb, output_prev_frame_vb, output_curr_frame_vb, output_next_frame_vb, output_img_path2_vb], show_progress=False)
        use_back_button_vb.click(video_blender_prev_frame, inputs=[input_text_frame_vb], outputs=[input_text_frame_vb, output_img_path1_vb, output_prev_frame_vb, output_curr_frame_vb, output_next_frame_vb, output_img_path2_vb], show_progress=False)
        prev_xframes_button_vb.click(video_blender_skip_prev, inputs=[input_text_frame_vb], outputs=[input_text_frame_vb, output_img_path1_vb, output_prev_frame_vb, output_curr_frame_vb, output_next_frame_vb, output_img_path2_vb], show_progress=False)
        next_xframes_button_vb.click(video_blender_skip_next, inputs=[input_text_frame_vb], outputs=[input_text_frame_vb, output_img_path1_vb, output_prev_frame_vb, output_curr_frame_vb, output_next_frame_vb, output_img_path2_vb], show_progress=False)
        preview_video_vb.click(video_blender_preview_video, inputs=input_project_path_vb, outputs=[tabs_video_blender, preview_path_vb])
        render_video_vb.click(video_blender_render_preview, inputs=[preview_path_vb, input_frame_rate_vb], outputs=[video_preview_vb])


    return app

if __name__ == '__main__':
    main()
