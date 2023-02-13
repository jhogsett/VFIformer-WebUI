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
from webui_utils.auto_increment import AutoIncrementDirectory
from webui_utils.image_utils import create_gif
from webui_utils.file_utils import create_directories, create_zip, get_files, create_directory
from webui_utils.simple_utils import max_steps, restored_frame_fractions, restored_frame_predictions
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
        print("The models are lazy-loaded on the first interpolation (so it'll be slow)")

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

        with gr.Tab("Resynthesize Video"):
            gr.HTML("Interpolate replacement frames from an entire video for use in video restoration", elem_id="tabheading")
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    input_path_text_rv = gr.Text(max_lines=1, placeholder="Path on this server to the frame PNG files", label="Input Path")
                    output_path_text_rv = gr.Text(max_lines=1, placeholder="Where to place the generated frames, leave blank to use default", label="Output Path")
            gr.Markdown("Note the first and last frames cannot be resynthesized. *Progress can be tracked in the console*")
            resynthesize_button_rv = gr.Button("Resynthesize Video (this will take time)", variant="primary")

        with gr.Tab("Frame Restoration"):
            gr.HTML("Restore multiple adjacent bad frames using precision interpolation", elem_id="tabheading")
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    with gr.Row(variant="compact"):
                        img1_input_fr = gr.Image(type="filepath", label="Frame before replacement frames", tool=None)
                        img2_input_fr = gr.Image(type="filepath", label="Frame after replacement frames", tool=None)
                    with gr.Row(variant="compact"):
                        frames_input_fr = gr.Slider(value=config.restoration_settings["default_frames"], minimum=1, maximum=config.restoration_settings["max_frames"], step=1, label="Frames to restore")
                        precision_input_fr = gr.Slider(value=config.restoration_settings["default_precision"], minimum=1, maximum=config.restoration_settings["max_precision"], step=1, label="Search Precision")
                    with gr.Row(variant="compact"):
                        times_default = restored_frame_fractions(config.restoration_settings["default_frames"])
                        times_output_fr = gr.Textbox(value=times_default, label="Frame Search Times", max_lines=1, interactive=False)
                with gr.Column(variant="panel"):
                    img_output_fr = gr.Image(type="filepath", label="Animated Preview", interactive=False)
                    file_output_fr = gr.File(type="file", file_count="multiple", label="Download", visible=False)
            predictions_default = restored_frame_predictions(config.restoration_settings["default_frames"], config.restoration_settings["default_precision"])
            predictions_output_fr = gr.Textbox(value=predictions_default, label="Predicted matches", max_lines=1, interactive=False)
            restore_button_fr = gr.Button("Restore Frames", variant="primary")

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
                                input_text_frame_vb = gr.Textbox(value="0", label="Frame")
                            with gr.Row():
                                prev_xframes_button_vb = gr.Button("<< Skip")
                                next_xframes_button_vb = gr.Button("Skip >>")
                        with gr.Column():
                            output_img_path2_vb = gr.Image(label="Repair / Path 2 Frame", interactive=False, type="filepath")
                        with gr.Column():
                            use_path_1_button_vb = gr.Button("Use Path 1 Frame | Next >", variant="primary")
                            use_path_2_button_vb = gr.Button("Use Path 2 Frame | Next >", variant="primary")
                            use_back_button_vb = gr.Button("< Back", variant="primary")
                with gr.Tab("Video Preview", id=2):
                    gr.Markdown("A way to preview the video is envisioned")

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
                            input_step_text = gr.Text(value="1", max_lines=1, placeholder="Integer step for the sequentially numbered files", label="Integer step")
                            input_zerofill_text = gr.Text(value="-1", max_lines=1, placeholder="Padding with for sequential numbers, -1=auto", label="Number Padding")
                        with gr.Row(variant="compact"):
                            input_rename_check = gr.Checkbox(value=False, label="Rename instead of duplicate files")
                        resequence_button = gr.Button("Resequence Files", variant="primary")
            with gr.Tab("Upscaling"):
                gr.Markdown("Use Real-ESRGAN 4x+ to restore and/or upscale images")
            with gr.Tab("gif2png"):
                gr.Markdown("Convert a GIF to a PNG sequence")
            with gr.Tab("mp42png"):
                gr.Markdown("Convert a MP4 to a PNG sequence")
            with gr.Tab("png2gif"):
                gr.Markdown("Convert a PNG sequence to a GIF, specify duration and looping")
            with gr.Tab("png2mp4"):
                gr.Markdown("Convert a PNG sequence to a MP4")
        with gr.Tab("Gif2Mp4"):
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    gr.Markdown("""
                    Idea: Recover the original video from animated GIF file
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

    return app

if __name__ == '__main__':
    main()
