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
from resequence_files import ResequenceFiles
from webui_utils.auto_increment import AutoIncrementDirectory

class ResynthesizeVideo():
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
        with gr.Tab("Resynthesize Video"):
            gr.HTML(SimpleIcons.TWO_HEARTS + "Interpolate replacement frames from an entire video for use in movie restoration", elem_id="tabheading")
            with gr.Row():
                with gr.Column():
                    e["input_path_text_rv"] = gr.Text(max_lines=1, placeholder="Path on this server to the frame PNG files", label="Input Path")
                    e["output_path_text_rv"] = gr.Text(max_lines=1, placeholder="Where to place the generated frames, leave blank to use default", label="Output Path")
            gr.Markdown("*Progress can be tracked in the console*")
            e["resynthesize_button_rv"] = gr.Button("Resynthesize Video " + SimpleIcons.SLOW_SYMBOL, variant="primary")
            with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
                WebuiTips.resynthesize_video.render()
        e["resynthesize_button_rv"].click(self.resynthesize_video, inputs=[e["input_path_text_rv"], e["output_path_text_rv"]])
        return e

    def resynthesize_video(self, input_path : str, output_path : str | None):
        if input_path:
            interpolater = Interpolate(self.engine.model, self.log)
            deep_interpolater = DeepInterpolate(interpolater, self.log)
            series_interpolater = InterpolateSeries(deep_interpolater, self.log)
            base_output_path = output_path or self.config.directories["output_resynthesis"]
            create_directory(base_output_path)
            output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
            output_basename = "resynthesized_frames"

            file_list = get_files(input_path, extension="png")
            self.log(f"beginning series of frame recreations at {output_path}")
            series_interpolater.interpolate_series(file_list, output_path, 1, output_basename, offset=2)
            self.log(f"auto-resequencing recreated frames at {output_path}")
            ResequenceFiles(output_path, "png", "resynthesized_frame", 1, 1, -1, True, self.log).resequence()
