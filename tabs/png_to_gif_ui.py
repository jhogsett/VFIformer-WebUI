from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from webui_utils.file_utils import create_directory, split_filepath
from webui_utils.video_utils import PNGtoGIF as _PNGtoGIF
from webui_tips import WebuiTips
from interpolate_engine import InterpolateEngine

class PNGtoGIF():
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
        with gr.Tab(SimpleIcons.CONV_SYMBOL + "PNG Sequence to GIF"):
            gr.Markdown("Convert a PNG sequence to a GIF")
            # e["input_path_text_pg"] = gr.Text(max_lines=1, label="PNG Files Path", placeholder="Path on this server to the PNG files to be converted")
            # e["output_path_text_pg"] = gr.Text(max_lines=1, label="GIF File", placeholder="Path and filename on this server for the converted GIF file")
            # e["input_pattern_text_pg"] = gr.Text(max_lines=1, label="Input Filename Pattern", placeholder="Pattern like image%03d.png (auto=automatic pattern)")

            with gr.Row():
                e["input_path_text_pg"] = gr.Text(max_lines=1, label="PNG Files Path", placeholder="Path on this server to the PNG files to be converted")
                e["output_path_text_pg"] = gr.Text(max_lines=1, label="GIF File", placeholder="Path and filename on this server for the converted GIF file")
            with gr.Row():
                e["input_pattern_text_pg"] = gr.Text(max_lines=1, label="Input Filename Pattern", placeholder="Pattern like image%03d.png (auto=automatic pattern)")
                e["framerate_pg"] = gr.Slider(value=30, minimum=1, maximum=240, step=1, label="GIF Frame Rate")

            with gr.Row():
                e["convert_button_pg"] = gr.Button("Convert", variant="primary")
                e["output_info_text_pg"] = gr.Textbox(label="Details", interactive=False)
            with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Guide", open=False):
                WebuiTips.png_to_gif.render()
        e["convert_button_pg"].click(self.convert_png_to_gif, inputs=[e["input_path_text_pg"], e["input_pattern_text_pg"], e["output_path_text_pg"], e["framerate_pg"]], outputs=e["output_info_text_pg"])

        # e["convert_button_pg"].click(webui_events.convert_png_to_gif, inputs=[e["input_path_text_pg"], e["input_pattern_text_pg"], e["output_path_text_pg"], e["framerate_pg"]], outputs=e["output_info_text_pg"])

        return e

    def convert_png_to_gif(self, input_path : str, input_pattern : str, output_filepath : str, frame_rate : int):
        if input_path and input_pattern and output_filepath:
            directory, _, _ = split_filepath(output_filepath)
            create_directory(directory)
            ffmpeg_cmd = _PNGtoGIF(input_path, input_pattern, output_filepath, frame_rate)
            return gr.update(value=ffmpeg_cmd, visible=True)
