from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from interpolate_engine import InterpolateEngine

class Resources():
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
        with gr.Tab(SimpleIcons.GLOBE + "Resources"):
            self.link_item("linkcontainer", "FFmpeg (Free Download)", "Download FFmpeg", "https://ffmpeg.org/download.html")
            self.link_item("linkcontainer2", "Adobe AI-Based Speech Enhancement (Free)", "Adobe Podcast (Beta) Enhance Speech", "https://podcast.adobe.com/enhance")
            self.link_item("linkcontainer", "Real-ESRGAN Image/Video Restoration (Github)", "Practical Algorithms for General Image/Video Restoration", "https://github.com/xinntao/Real-ESRGAN")
            self.link_item("linkcontainer2", "Coqui TTS (Python)", "Advanced Text-to-Speech generation", "https://pypi.org/project/TTS/")
            self.link_item("linkcontainer", "Motion Array (Royalty-Free Content)", "The All-in-One Video &amp; Filmmakers Platform", "https://motionarray.com/")
        return e

    def link_item(self, container_id : str, title : str, label : str, url : str):
        with gr.Row(variant="panel", elem_id=container_id) as row:
            gr.HTML(f"""
<div id="{container_id}">
    <p id="linkitem">
        {SimpleIcons.GLOBE}{title} -
        <a href="{url}" target="_blank">{label}</a>
    </p>
</div>""")
        return row