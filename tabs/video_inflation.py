from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from webui_utils.file_utils import create_directory, get_files
from webui_tips import WebuiTips
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from deep_interpolate import DeepInterpolate
from interpolate_series import InterpolateSeries
from webui_utils.auto_increment import AutoIncrementDirectory
from webui_utils.ui_utils import update_splits_info

class VideoInflation():
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
        with gr.Tab("Video Inflation"):
            gr.HTML(SimpleIcons.BALLOON + "Double the number of video frames to any depth for super slow motion", elem_id="tabheading")
            with gr.Row():
                with gr.Column():
                    e["input_path_text_vi"] = gr.Text(max_lines=1, placeholder="Path on this server to the frame PNG files", label="Input Path")
                    e["output_path_text_vi"] = gr.Text(max_lines=1, placeholder="Where to place the generated frames, leave blank to use default", label="Output Path")
                    with gr.Row():
                        e["splits_input_vi"] = gr.Slider(value=1, minimum=1, maximum=10, step=1, label="Split Count")
                        e["info_output_vi"] = gr.Textbox(value="1", label="Interpolations per Frame", max_lines=1, interactive=False)
            gr.Markdown("*Progress can be tracked in the console*")
            e["interpolate_button_vi"] = gr.Button("Inflate Video " + SimpleIcons.SLOW_SYMBOL, variant="primary")
            with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Guide", open=False):
                WebuiTips.video_inflation.render()
        e["interpolate_button_vi"].click(self.video_inflation, inputs=[e["input_path_text_vi"], e["output_path_text_vi"], e["splits_input_vi"]])
        e["splits_input_vi"].change(update_splits_info, inputs=e["splits_input_vi"], outputs=e["info_output_vi"], show_progress=False)
        return e

    def video_inflation(self, input_path : str, output_path : str | None, num_splits : float):
        if input_path:
            interpolater = Interpolate(self.engine.model, self.log)
            deep_interpolater = DeepInterpolate(interpolater, self.log)
            series_interpolater = InterpolateSeries(deep_interpolater, self.log)
            base_output_path = output_path or self.config.directories["output_inflation"]
            create_directory(base_output_path)
            output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
            output_basename = "interpolated_frames"
            file_list = get_files(input_path, extension="png")

            self.log(f"beginning series of deep interpolations at {output_path}")
            series_interpolater.interpolate_series(file_list, output_path, num_splits, output_basename)
