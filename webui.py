import os
import time
import signal
import argparse
import gradio as gr
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from deep_interpolate import DeepInterpolate
from simple_log import SimpleLog
from simple_config import SimpleConfig
from auto_increment import AutoIncrementFilename, AutoIncrementDirectory
from image_utils import create_gif
from file_utils import create_directories, create_zip
from simple_utils import max_steps

global restart, prevent_inbrowser
restart = False
prevent_inbrowser = False

def main():
    global log, config, engine, restart, prevent_inbrowser
    parser = argparse.ArgumentParser(description='VFIformer Web UI')
    parser.add_argument("--config_path", type=str, default="config.yaml", help="path to config YAML file")
    parser.add_argument("--verbose", dest="verbose", default=False, action="store_true", help="Show extra details")
    args = parser.parse_args()

    log = SimpleLog(args.verbose)
    config = SimpleConfig(args.config_path).config_obj()
    create_directories(config.directories)
    engine = InterpolateEngine(config.model, config.gpu_ids)

    print("Starting VFIformer-WebUI")
    print("The models are lazy-loaded on the first interpolation (so it'll be slow)")
    while True:
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

def deep_interpolate(img_before_file : str, img_after_file : str, num_splits : float):
    global log, config, engine, file_output
    file_output.update(visible=False)

    if img_before_file and img_after_file:
        interpolater = Interpolate(engine.model, log.log)
        deep_interpolater = DeepInterpolate(interpolater, log.log)
        base_output_path = config.directories["output_interpolate"]
        output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
        output_basename = "interpolated_frames"

        # extension = "png"
        # preview_file, image_index = AutoIncrementFilename(output_path, extension).next_filename(output_basename, extension)

        log.log(f"creating frame files at {output_path}")
        deep_interpolater.split_frames(img_before_file, img_after_file, num_splits, output_path, output_basename)
        output_paths = deep_interpolater.output_paths

        # name the gif for the directory run number in case of comparing files from multiple directories
        preview_gif = os.path.join(output_path, output_basename + str(run_index) + ".gif")
        log.log(f"creating preview file {preview_gif}")
        duration = config.interpolate_settings["gif_duration"] / len(output_paths)
        create_gif(output_paths, preview_gif, duration=duration)

        # name the zip for the directory run number in case of using zips from multiple directories
        download_zip = os.path.join(output_path, output_basename + str(run_index) + ".zip")
        log.log("creating zip of frame files")
        create_zip(output_paths, download_zip)

        downloads = [preview_gif, download_zip]

        return gr.Image.update(value=preview_gif), gr.File.update(value=downloads, visible=True)
    else:
        return None, None

def update_splits_info(num_splits : float):
    return str(max_steps(num_splits))

def restart_app():
    global restart
    restart = True

#### Create Gradio UI

def create_ui():
    global config, file_output
    with gr.Blocks(analytics_enabled=False, 
                    title="VFIformer Web UI", 
                    theme=config.user_interface["theme"],
                    css=config.user_interface["css_file"]) as app:
        gr.Markdown("VFIformer Web UI")
        with gr.Tab("Frame Interpolation"):
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    img1_input = gr.Image(type="filepath", label="Before Image", tool=None)
                    img2_input = gr.Image(type="filepath", label="After Image", tool=None)
                    with gr.Row(variant="panel"):
                        splits_input = gr.Slider(value=1, minimum=1, maximum=10, step=1, label="Splits")
                        info_output = gr.Textbox(value="1", label="New Frames", max_lines=1, interactive=False)
                with gr.Column(variant="panel"):
                    img_output = gr.Image(type="filepath", label="Animated Preview", interactive=False)
                    file_output = gr.File(type="file", file_count="multiple", label="Download", visible=False)
            interpolate_button = gr.Button("Interpolate", variant="primary")
        with gr.Tab("Video Inflation"):
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    gr.Markdown("""
                    # Inflate a video, both in resolution and frame rate
                    - split video into a series of PNG frames
                    - use R-ESRGAN 4x+ to restore and/or upscale
                    - use VFIformer to:
                      - increase frame rate, or
                      - create super slow motion, or
                      - reconstruct timelapsed video
                    - reassemble new PNG frames into MP4 file
                    """)
        with gr.Tab("gif2mp4"):
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    gr.Markdown("""
                    # Recover the original video from animated GIF file
                    - split GIF into a series of PNG frames
                    - use R-ESRGAN 4x+ to restore and/or upscale
                    - use VFIformer to adjust frame rate to real time
                    - reassemble new PNG frames into MP4 file
                    """)
        with gr.Tab("Tools"):
            with gr.Row(variant="compact"):
                restart_button = gr.Button("Restart App", variant="primary")
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    gr.Markdown("""
                    # Tools
                    - split a GIF or MP4 into a series of PNG frames
                    - rename a sequence of PNG files suitable for import into Premiere Pro
                    - recombine a series of PNG frames into an MP4
                    - ?
                    """)
        interpolate_button.click(deep_interpolate, inputs=[img1_input, img2_input, splits_input], outputs=[img_output, file_output])
        splits_input.change(update_splits_info, inputs=splits_input, outputs=info_output, show_progress=False)
        restart_button.click(restart_app, _js="setTimeout(function(){location.reload()},500)")
    return app

if __name__ == '__main__':
    main()
