from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from webui_utils.file_utils import create_directory
from webui_utils.auto_increment import AutoIncrementDirectory
from webui_tips import WebuiTips
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from interpolation_target import TargetInterpolate
from resample_series import ResampleSeries
from resequence_files import ResequenceFiles
from webui_utils.simple_utils import fps_change_details
from webui_utils.ui_utils import update_info_fc

class ChangeFPS():
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
        max_fps = self.config.fps_change_settings["maximum_fps"]
        starting_fps = self.config.fps_change_settings["starting_fps"]
        ending_fps = self.config.fps_change_settings["ending_fps"]
        max_precision = self.config.fps_change_settings["max_precision"]
        precision = self.config.fps_change_settings["default_precision"]
        lowest_common_rate, filled, sampled, fractions, predictions = fps_change_details(starting_fps, ending_fps, precision)
        e = {}
        with gr.Tab(SimpleIcons.FILM + "Change FPS"):
            gr.HTML("Change the frame rate for a set of PNG video frames using frame search", elem_id="tabheading")
            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        e["input_path_text_fc"] = gr.Text(max_lines=1, label="Input Path", placeholder="Path on this server to the PNG frame files to be converted")
                        e["output_path_text_fc"] = gr.Text(max_lines=1, label="Output Path", placeholder="Path on this server for the converted PNG frame files, leave blank to use default")
                    with gr.Row():
                        e["starting_fps_fc"] = gr.Slider(value=starting_fps, minimum=1, maximum=max_fps, step=1, label="Starting FPS")
                        e["ending_fps_fc"] = gr.Slider(value=ending_fps, minimum=1, maximum=max_fps, step=1, label="Ending FPS")
                        e["output_lcm_text_fc"] = gr.Text(value=lowest_common_rate, max_lines=1, label="Lowest Common FPS", interactive=False)
                        e["output_filler_text_fc"] = gr.Text(value=filled, max_lines=1, label="Filled Frames per Input Frame", interactive=False)
                        e["output_sampled_text_fc"] = gr.Text(value=sampled, max_lines=1, label="Output Frames Sample Rate", interactive=False)
                    with gr.Row():
                        e["precision_fc"] = gr.Slider(value=precision, minimum=1, maximum=max_precision, step=1, label="Precision")
                        e["times_output_fc"] = gr.Textbox(value=fractions, label="Frame Search Times", max_lines=8, interactive=False)
                        e["predictions_output_fc"] = gr.Textbox(value=predictions, label="Predicted Matches", max_lines=8, interactive=False)
            gr.Markdown("*Progress can be tracked in the console*")
            e["convert_button_fc"] = gr.Button("Convert " + SimpleIcons.SLOW_SYMBOL, variant="primary")
            with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Guide", open=False):
                WebuiTips.change_fps.render()
        e["starting_fps_fc"].change(update_info_fc, inputs=[e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]], outputs=[e["output_lcm_text_fc"], e["output_filler_text_fc"], e["output_sampled_text_fc"], e["times_output_fc"], e["predictions_output_fc"]], show_progress=False)
        e["ending_fps_fc"].change(update_info_fc, inputs=[e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]], outputs=[e["output_lcm_text_fc"], e["output_filler_text_fc"], e["output_sampled_text_fc"], e["times_output_fc"], e["predictions_output_fc"]], show_progress=False)
        e["precision_fc"].change(update_info_fc, inputs=[e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]], outputs=[e["output_lcm_text_fc"], e["output_filler_text_fc"], e["output_sampled_text_fc"], e["times_output_fc"], e["predictions_output_fc"]], show_progress=False)
        e["convert_button_fc"].click(self.convert_fc, inputs=[e["input_path_text_fc"], e["output_path_text_fc"], e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]])
        return e

    def convert_fc(self, input_path : str, output_path : str, starting_fps : int, ending_fps : int, precision : int):
        if input_path:
            interpolater = Interpolate(self.engine.model, self.log)
            target_interpolater = TargetInterpolate(interpolater, self.log)
            series_resampler = ResampleSeries(target_interpolater, self.log)
            if output_path:
                base_output_path = output_path
                create_directory(base_output_path)
            else:
                base_output_path, _ = AutoIncrementDirectory(self.config.directories["output_fps_change"]).next_directory("run")
            series_resampler.resample_series(input_path, base_output_path, starting_fps, ending_fps, precision, f"resampled@{starting_fps}")

            self.log(f"auto-resequencing sampled frames at {output_path}")
            ResequenceFiles(base_output_path, "png", f"resampled@{ending_fps}fps", 0, 1, -1, True, self.log).resequence()
