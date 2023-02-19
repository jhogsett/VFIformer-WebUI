import os
from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from webui_utils.image_utils import create_gif
from webui_utils.file_utils import create_zip
from webui_utils.ui_utils import update_splits_info, create_report
from webui_tips import WebuiTips
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from deep_interpolate import DeepInterpolate
from webui_utils.auto_increment import AutoIncrementDirectory

class FrameInterpolation():
    def __init__(self,
                    config : SimpleConfig,
                    engine : InterpolateEngine,
                    log_fn : Callable):
        self.engine = engine
        self.config = config
        self.log_fn = log_fn

    def log(self, message : str):
        self.log_fn(message)

    def render_tab(self):
        e = {}
        with gr.Tab("Frame Interpolation"):
            gr.HTML(SimpleIcons.DIVIDE + "Divide the time between two frames to any depth, see an animation of result and download the new frames", elem_id="tabheading")
            with gr.Row():
                with gr.Column():
                    e["img1_input_fi"] = gr.Image(type="filepath", label="Before Frame", tool=None)
                    e["img2_input_fi"] = gr.Image(type="filepath", label="After Frame", tool=None)
                    with gr.Row():
                        e["splits_input_fi"] = gr.Slider(value=1, minimum=1, maximum=self.config.interpolation_settings["max_splits"], step=1, label="Split Count")
                        e["info_output_fi"] = gr.Textbox(value="1", label="Interpolated Frames", max_lines=1, interactive=False)
                with gr.Column():
                    e["img_output_fi"] = gr.Image(type="filepath", label="Animated Preview", interactive=False, elem_id="mainoutput")
                    e["file_output_fi"] = gr.File(type="file", file_count="multiple", label="Download", visible=False)
            e["interpolate_button_fi"] = gr.Button("Interpolate", variant="primary")
            with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Guide", open=False):
                WebuiTips.frame_interpolation.render()

        e["interpolate_button_fi"].click(self.frame_interpolation, inputs=[e["img1_input_fi"], e["img2_input_fi"], e["splits_input_fi"]], outputs=[e["img_output_fi"], e["file_output_fi"]])
        e["splits_input_fi"].change(update_splits_info, inputs=e["splits_input_fi"], outputs=e["info_output_fi"], show_progress=False)
        return e

    def frame_interpolation(self, img_before_file : str, img_after_file : str, num_splits : float):
        if img_before_file and img_after_file:
            interpolater = Interpolate(self.engine.model, self.log_fn)
            deep_interpolater = DeepInterpolate(interpolater, self.log_fn)
            base_output_path = self.config.directories["output_interpolation"]
            output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
            output_basename = "interpolated_frames"

            self.log(f"creating frame files at {output_path}")
            deep_interpolater.split_frames(img_before_file, img_after_file, num_splits, output_path, output_basename)
            output_paths = deep_interpolater.output_paths

            downloads = []
            preview_gif = None
            if self.config.interpolation_settings["create_gif"]:
                preview_gif = os.path.join(output_path, output_basename + str(run_index) + ".gif")
                self.log(f"creating preview file {preview_gif}")
                duration = self.config.interpolation_settings["gif_duration"] / len(output_paths)
                create_gif(output_paths, preview_gif, duration=duration)
                downloads.append(preview_gif)

            if self.config.interpolation_settings["create_zip"]:
                download_zip = os.path.join(output_path, output_basename + str(run_index) + ".zip")
                self.log("creating zip of frame files")
                create_zip(output_paths, download_zip)
                downloads.append(download_zip)

            if self.config.interpolation_settings["create_txt"]:
                info_file = os.path.join(output_path, output_basename + str(run_index) + ".txt")
                create_report(info_file, img_before_file, img_after_file, num_splits, output_path, output_paths)
                downloads.append(info_file)

            return gr.Image.update(value=preview_gif), gr.File.update(value=downloads, visible=True)
        else:
            return None, None
