import os
import time
import signal
import argparse
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

log = None
config = None
engine= None
restart = False
prevent_inbrowser = False

def main():
    global log, config, engine, prevent_inbrowser
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
        # interpolater = Interpolate(engine.model, log.log)
        # deep_interpolater = DeepInterpolate(interpolater, log.log)
        # series_interpolater = InterpolateSeries(deep_interpolater, log.log)
        # base_output_path = output_path or config.directories["output_inflation"]
        # create_directory(base_output_path)
        # output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
        # output_basename = "interpolated_frames"
        # file_list = get_files(input_path, extension="png")

        # log.log(f"beginning series of deep interpolations at {output_path}")
        # series_interpolater.interpolate_series(file_list, output_path, num_splits, output_basename)
        log.log(f"awaiting implementation")

def resequence_files(input_path : str, input_filetype : str, input_newname : str, input_start : str, input_step : str, input_zerofill : str, input_rename_check : bool):
    global log
    if input_path and input_filetype and input_newname and input_start and input_step and input_zerofill:
        ResequenceFiles(input_path, input_filetype, input_newname, int(input_start), int(input_step), int(input_zerofill), input_rename_check, log.log).resequence()

def frame_restoration(img_before_file : str, img_after_file : str, num_frames : float, num_splits : float):
    return #gr.Image.update(value=preview_gif), gr.File.update(value=downloads, visible=True)

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
    global config, file_output, file_output2
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
            gr.HTML("Interpolate all-new frames from a video for use in restoration restored frames", elem_id="tabheading")
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    input_path_text_rv = gr.Text(max_lines=1, placeholder="Path on this server to the frame PNG files", label="Input Path")
                    output_path_text_rv = gr.Text(max_lines=1, placeholder="Where to place the generated frames, leave blank to use default", label="Output Path")
            gr.Markdown("*Progress can be tracked in the console*")
            resynthesize_button_rv = gr.Button("Resynthesize Video (this will take time)", variant="primary")

        with gr.Tab("Frame Restoration"):
            gr.HTML("Restore two or more adjacent restored frames using Frame Search and download the restored frames", elem_id="tabheading")
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    with gr.Row(variant="compact"):
                        img1_input_fr = gr.Image(type="filepath", label="Frame before first restored one", tool=None, shape=(192, 108))
                        img2_input_fr = gr.Image(type="filepath", label="Frame after last restored one", tool=None, shape=(192, 108))
                    with gr.Row(variant="compact"):
                        frames_input_fr = gr.Slider(value=config.restoration_settings["default_frames"], minimum=1, maximum=config.restoration_settings["max_frames"], step=1, label="Frames to restore")
                        precision_input_fr = gr.Slider(value=config.restoration_settings["default_precision"], minimum=1, maximum=config.restoration_settings["max_precision"], step=1, label="Search Precision")
                with gr.Column(variant="panel"):
                    img_output_fr = gr.Image(type="filepath", label="Animated Preview", interactive=False)
                    file_output_fr = gr.File(type="file", file_count="multiple", label="Download", visible=False)
            times_default = restored_frame_fractions(config.restoration_settings["default_frames"])
            predictions_default = restored_frame_predictions(config.restoration_settings["default_frames"], config.restoration_settings["default_precision"])
            times_output_fr = gr.Textbox(value=times_default, label="Frame Search Times", max_lines=1, interactive=False)
            predictions_output_fr = gr.Textbox(value=predictions_default, label="Predicted matches", max_lines=1, interactive=False)
            restore_button_fr = gr.Button("Restore Frames", variant="primary")

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

        restart_button.click(restart_app, _js="setTimeout(function(){location.reload()},1000)")

        resequence_button.click(resequence_files, inputs=[input_path_text2, input_filetype_text, input_newname_text, input_start_text, input_step_text, input_zerofill_text, input_rename_check])

        restore_button_fr.click(frame_restoration, inputs=[img1_input_fr, img2_input_fr, frames_input_fr, precision_input_fr], outputs=[img_output_fr, file_output_fr])
        frames_input_fr.change(update_info_fr, inputs=[frames_input_fr, precision_input_fr], outputs=[times_output_fr, predictions_output_fr], show_progress=False)
        precision_input_fr.change(update_info_fr, inputs=[frames_input_fr, precision_input_fr], outputs=[times_output_fr, predictions_output_fr], show_progress=False)

    return app

if __name__ == '__main__':
    main()
