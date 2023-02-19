from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from webui_utils.file_utils import create_directory, split_filepath
from webui_utils.video_utils import PNGtoMP4 as _PNGtoMP4
from webui_tips import WebuiTips
from interpolate_engine import InterpolateEngine

class PNGtoMP4():
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
        with gr.Tab(SimpleIcons.CONV_SYMBOL + "PNG Sequence to MP4"):
            gr.Markdown("Convert a PNG sequence to a MP4")
            e["input_path_text_pm"] = gr.Text(max_lines=1, label="PNG Files Path", placeholder="Path on this server to the PNG files to be converted")
            e["output_path_text_pm"] = gr.Text(max_lines=1, label="MP4 File", placeholder="Path and filename on this server for the converted MP4 file")
            with gr.Row():
                e["input_pattern_text_pm"] = gr.Text(max_lines=1, label="Input Filename Pattern", placeholder="Pattern like image%03d.png (auto=automatic pattern)")
                e["input_frame_rate_pm"] = gr.Slider(minimum=1, maximum=60, value=self.config.png_to_mp4_settings["frame_rate"], step=1, label="Frame Rate")
                e["quality_slider_pm"] = gr.Slider(minimum=self.config.png_to_mp4_settings["minimum_crf"], maximum=self.config.png_to_mp4_settings["maximum_crf"], step=1, value=self.config.png_to_mp4_settings["default_crf"], label="Quality (lower=better)")
            with gr.Row():
                e["convert_button_pm"] = gr.Button("Convert", variant="primary")
                e["output_info_text_pm"] = gr.Textbox(label="Details", interactive=False)
            with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
                WebuiTips.png_to_mp4.render()
        e["convert_button_pm"].click(self.convert_png_to_mp4, inputs=[e["input_path_text_pm"], e["input_pattern_text_pm"], e["input_frame_rate_pm"], e["output_path_text_pm"], e["quality_slider_pm"]], outputs=e["output_info_text_pm"])
        return e

    def convert_png_to_mp4(self, input_path : str, input_pattern : str, frame_rate : int, output_filepath: str, quality : str):
        if input_path and input_pattern and output_filepath:
            directory, _, _ = split_filepath(output_filepath)
            create_directory(directory)
            ffmpeg_cmd = _PNGtoMP4(input_path, input_pattern, int(frame_rate), output_filepath, crf=quality)
            return gr.update(value=ffmpeg_cmd, visible=True)
