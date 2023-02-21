"""GIF to PNG Sequence feature UI and event handlers"""
from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from scripts.interpolate_engine import InterpolateEngine

class Options():
    """Encapsulates UI elements and events for the MP4 to PNG Sequence feature"""
    def __init__(self,
                    config : SimpleConfig,
                    engine : InterpolateEngine,
                    log_fn : Callable,
                    restart_fn : Callable):
        self.engine = engine
        self.config = config
        self.log_fn = log_fn
        self.restart_fn = restart_fn

    def log(self, message : str):
        """Logging"""
        self.log_fn(message)

    def render_tab(self):
        """Render tab into UI"""
        with gr.Tab(SimpleIcons.GEAR + "Options"):
            with gr.Row():
                restart_button = gr.Button("Restart App", variant="primary",
                    elem_id="restartbutton").style(full_width=False)
        restart_button.click(self.restart_fn,
            _js="function(){setTimeout(function(){window.location.reload()},2000);return[]}")
