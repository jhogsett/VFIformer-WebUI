from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from webui_utils.file_utils import create_directory
from webui_tips import WebuiTips
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from interpolation_target import TargetInterpolate
from webui_utils.auto_increment import AutoIncrementDirectory

class FrameSearch():
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
        max_splits = self.config.search_settings["max_splits"]
        e = {}
        with gr.Tab("Frame Search"):
            gr.HTML(SimpleIcons.MAGNIFIER + "Search for an arbitrarily precise timed frame and return the closest match", elem_id="tabheading")
            with gr.Row():
                with gr.Column():
                    e["img1_input_fs"] = gr.Image(type="filepath", label="Before Frame", tool=None)
                    e["img2_input_fs"] = gr.Image(type="filepath", label="After Frame", tool=None)
                    with gr.Row():
                        e["splits_input_fs"] = gr.Slider(value=1, minimum=1, maximum=max_splits, step=1, label="Search Precision")
                        e["min_input_text_fs"] = gr.Text(placeholder="0.0-1.0", label="Lower Bound")
                        e["max_input_text_fs"] = gr.Text(placeholder="0.0-1.0", label="Upper Bound")
                with gr.Column():
                    e["img_output_fs"] = gr.Image(type="filepath", label="Found Frame", interactive=False, elem_id="mainoutput")
                    e["file_output_fs"] = gr.File(type="file", file_count="multiple", label="Download", visible=False)
            e["search_button_fs"] = gr.Button("Search", variant="primary")
            with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Guide", open=False):
                WebuiTips.frame_search.render()
        e["search_button_fs"].click(self.frame_search, inputs=[e["img1_input_fs"], e["img2_input_fs"], e["splits_input_fs"], e["min_input_text_fs"], e["max_input_text_fs"]], outputs=[e["img_output_fs"], e["file_output_fs"]])
        return e

    def frame_search(self, img_before_file : str, img_after_file : str, num_splits : float, min_target : float, max_target : float):
        if img_before_file and img_after_file and min_target and max_target:
            interpolater = Interpolate(self.engine.model, self.log)
            target_interpolater = TargetInterpolate(interpolater, self.log)
            base_output_path = self.config.directories["output_search"]
            create_directory(base_output_path)
            output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
            output_basename = "frame"

            self.log(f"beginning targeted interpolations at {output_path}")
            target_interpolater.split_frames(img_before_file, img_after_file, num_splits, float(min_target), float(max_target), output_path, output_basename)
            output_paths = target_interpolater.output_paths
            return gr.Image.update(value=output_paths[0]), gr.File.update(value=output_paths, visible=True)
