import os
from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from webui_utils.image_utils import create_gif
from webui_utils.file_utils import create_zip, create_directory
from webui_utils.ui_utils import create_report
from webui_tips import WebuiTips
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from interpolation_target import TargetInterpolate
from restore_frames import RestoreFrames
from webui_utils.auto_increment import AutoIncrementDirectory
from webui_utils.simple_utils import restored_frame_fractions, restored_frame_predictions
from webui_utils.ui_utils import update_info_fr

class FrameRestoration():
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
        with gr.Tab("Frame Restoration"):
            gr.HTML(SimpleIcons.MAGIC_WAND + "Restore multiple adjacent bad frames using precision interpolation", elem_id="tabheading")
            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        e["img1_input_fr"] = gr.Image(type="filepath", label="Frame Before Replacement Frames", tool=None)
                        e["img2_input_fr"] = gr.Image(type="filepath", label="Frame After Replacement Frames", tool=None)
                    with gr.Row():
                        e["frames_input_fr"] = gr.Slider(value=self.config.restoration_settings["default_frames"], minimum=1, maximum=self.config.restoration_settings["max_frames"], step=1, label="Frames to Restore")
                        e["precision_input_fr"] = gr.Slider(value=self.config.restoration_settings["default_precision"], minimum=1, maximum=self.config.restoration_settings["max_precision"], step=1, label="Search Precision")
                    with gr.Row():
                        times_default = restored_frame_fractions(self.config.restoration_settings["default_frames"])
                        e["times_output_fr"] = gr.Textbox(value=times_default, label="Frame Search Times", max_lines=1, interactive=False)
                with gr.Column():
                    e["img_output_fr"] = gr.Image(type="filepath", label="Animated Preview", interactive=False)
                    e["file_output_fr"] = gr.File(type="file", file_count="multiple", label="Download", visible=False)
            predictions_default = restored_frame_predictions(self.config.restoration_settings["default_frames"], self.config.restoration_settings["default_precision"])
            e["predictions_output_fr"] = gr.Textbox(value=predictions_default, label="Predicted Matches", max_lines=1, interactive=False)
            e["restore_button_fr"] = gr.Button("Restore Frames", variant="primary")
            with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Guide", open=False):
                WebuiTips.frame_restoration.render()
        e["restore_button_fr"].click(self.frame_restoration, inputs=[e["img1_input_fr"], e["img2_input_fr"], e["frames_input_fr"], e["precision_input_fr"]], outputs=[e["img_output_fr"], e["file_output_fr"]])
        e["frames_input_fr"].change(update_info_fr, inputs=[e["frames_input_fr"], e["precision_input_fr"]], outputs=[e["times_output_fr"], e["predictions_output_fr"]], show_progress=False)
        e["precision_input_fr"].change(update_info_fr, inputs=[e["frames_input_fr"], e["precision_input_fr"]], outputs=[e["times_output_fr"], e["predictions_output_fr"]], show_progress=False)
        return e

    def frame_restoration(self, img_before_file : str, img_after_file : str, num_frames : float, num_splits : float):
        if img_before_file and img_after_file:
            interpolater = Interpolate(self.engine.model, self.log)
            target_interpolater = TargetInterpolate(interpolater, self.log)
            frame_restorer = RestoreFrames(target_interpolater, self.log)
            base_output_path = self.config.directories["output_restoration"]
            create_directory(base_output_path)
            output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
            output_basename = "restored_frame"

            self.log(f"beginning frame restorations at {output_path}")
            frame_restorer.restore_frames(img_before_file, img_after_file, num_frames, num_splits, output_path, output_basename)
            output_paths = frame_restorer.output_paths

            downloads = []
            preview_gif = None
            if self.config.restoration_settings["create_gif"]:
                preview_gif = os.path.join(output_path, output_basename + str(run_index) + ".gif")
                self.log(f"creating preview file {preview_gif}")
                duration = self.config.restoration_settings["gif_duration"] / len(output_paths)
                gif_paths = [img_before_file, *output_paths, img_after_file]
                create_gif(gif_paths, preview_gif, duration=duration)
                downloads.append(preview_gif)

            if self.config.restoration_settings["create_zip"]:
                download_zip = os.path.join(output_path, output_basename + str(run_index) + ".zip")
                self.log("creating zip of frame files")
                create_zip(output_paths, download_zip)
                downloads.append(download_zip)

            if self.config.restoration_settings["create_txt"]:
                info_file = os.path.join(output_path, output_basename + str(run_index) + ".txt")
                create_report(info_file, img_before_file, img_after_file, num_splits, output_path, output_paths)
                downloads.append(info_file)

            return gr.Image.update(value=preview_gif), gr.File.update(value=downloads, visible=True)
