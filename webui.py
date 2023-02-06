import os
import argparse
import gradio as gr
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from deep_interpolate import DeepInterpolate
from simple_log import SimpleLog
from simple_config import SimpleConfig
from auto_increment import AutoIncrementFilename, AutoIncrementDirectory
from image_utils import create_gif
from file_utils import create_directories
from simple_utils import max_steps

def main():
    global log, config, engine
    parser = argparse.ArgumentParser(description='VFIformer Web UI')
    parser.add_argument("--config_path", type=str, default="config.yaml", help="path to config YAML file")
    parser.add_argument("--verbose", dest="verbose", default=False, action="store_true", help="Show extra details")
    args = parser.parse_args()

    log = SimpleLog(args.verbose)
    config = SimpleConfig(args.config_path).config_obj()
    create_directories(config.directories)
    engine = InterpolateEngine(config.model, config.gpu_ids)

    app = create_ui()
    app.launch(inbrowser = config.auto_launch_browser, 
                server_name = config.server_name,
                server_port = config.server_port)

def deep_interpolate(img_before_file : str, img_after_file : str, num_splits : float):
    global log, config, engine, file_output
    file_output.update(visible=False)

    if img_before_file and img_after_file:
        interpolater = Interpolate(engine.model, log.log)
        deep_interpolater = DeepInterpolate(interpolater, log.log)
        base_output_path = config.directories["output_interpolate"]
        output_path, _ = AutoIncrementDirectory(base_output_path).next_directory("run")
        output_basename = "interpolated_frames"
        extension = "png"
        img_between_file, image_index = AutoIncrementFilename(output_path, extension).next_filename(output_basename, extension)

        log.log("creating frame file " + img_between_file)
        deep_interpolater.split_frames(img_before_file, img_after_file, num_splits, output_path, output_basename)

        log.log("creating preview file " + img_between_file)
        img_output_gif = os.path.join(output_path, output_basename + str(image_index) + ".gif")
        output_paths = deep_interpolater.output_paths
        duration = config.interpolate_settings["gif_duration"] / len(output_paths)
        create_gif(output_paths, img_output_gif, duration=duration)

        download_visible = num_splits == 1
        download_file = img_between_file if download_visible else None
        return gr.Image.update(value=img_output_gif), gr.File.update(value=download_file, visible=download_visible)
    else:
        return None, None

def update_splits_info(num_splits : float):
    return str(max_steps(num_splits))

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
                    file_output = gr.File(type="file", label="Download", visible=False)
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
    return app

if __name__ == '__main__':
    main()
