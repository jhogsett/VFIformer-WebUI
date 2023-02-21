"""GIF to PNG Sequence feature UI and event handlers"""
from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from webui_utils.file_utils import create_directory
from webui_utils.video_utils import GIFtoPNG as _GIFtoPNG
from scripts.webui_tips import WebuiTips
from scripts.interpolate_engine import InterpolateEngine

class GIFtoPNG():
    """Encapsulates UI elements and events for the GIF to PNG Sequence feature"""
    def __init__(self,
                    config : SimpleConfig,
                    engine : InterpolateEngine,
                    log_fn : Callable):
        self.engine = engine
        self.config = config
        self.log_fn = log_fn

    def log(self, message : str):
        """Logging"""
        self.log_fn(message)

    def render_tab(self):
        """Render tab into UI"""
        with gr.Tab(SimpleIcons.CONV_SYMBOL + "GIF to PNG Sequence"):
            gr.Markdown("Convert GIF to a PNG sequence")
            input_path_text_gp = gr.Text(max_lines=1, label="GIF File",
                placeholder="Path on this server to the GIF file to be converted")
            output_path_text_gp = gr.Text(max_lines=1, label="PNG Files Path",
                placeholder="Path on this server to a directory for the converted PNG files")
            with gr.Row():
                convert_button_gp = gr.Button("Convert", variant="primary")
                output_info_text_gp = gr.Textbox(label="Details", interactive=False)
            with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Guide", open=False):
                WebuiTips.gif_to_png.render()
        convert_button_gp.click(self.convert_gif_to_png,
            inputs=[input_path_text_gp, output_path_text_gp], outputs=output_info_text_gp)

    def convert_gif_to_png(self, input_filepath : str, output_path : str):
        """Convert button handler"""
        if input_filepath and output_path:
            create_directory(output_path)
            ffmpeg_cmd = _GIFtoPNG(input_filepath, output_path)
            return gr.update(value=ffmpeg_cmd, visible=True)
