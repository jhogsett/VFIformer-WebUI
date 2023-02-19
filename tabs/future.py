from typing import Callable
import gradio as gr
from interpolate_engine import InterpolateEngine
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons

from webui_tips import WebuiTips

class Future():
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
        with gr.Tab(SimpleIcons.WISH_SYMBOL + "GIF to Video"):
            with gr.Row():
                with gr.Column():
                    WebuiTips.gif_to_mp4.render()

        with gr.Tab(SimpleIcons.WISH_SYMBOL + "Upscaling"):
            WebuiTips.upscaling.render()
        return e
