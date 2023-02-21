from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from interpolate_engine import InterpolateEngine

class Options():
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
        self.log_fn(message)

    def render_tab(self):
        e = {}
        with gr.Tab(SimpleIcons.GEAR + "Options"):
            with gr.Row():
                e["restart_button"] = gr.Button("Restart App", variant="primary", elem_id="restartbutton").style(full_width=False)
        e["restart_button"].click(self.restart_fn, _js="function(){setTimeout(function(){window.location.reload()},2000);return[]}")
        return e
