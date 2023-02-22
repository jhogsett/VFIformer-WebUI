"""Upscale Frames feature UI and event handlers"""
from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from webui_utils.file_utils import create_directory, get_files
from webui_utils.auto_increment import AutoIncrementDirectory
from webui_utils.ui_utils import update_splits_info
from webui_tips import WebuiTips
from upscale_series import UpscaleSeries

class UpscaleFrames():
    """Encapsulates UI elements and events for the Upscale Frames feature"""
    def __init__(self,
                    config : SimpleConfig,
                    engine : any,
                    log_fn : Callable):
        self.config = config
        self.log_fn = log_fn

    def log(self, message : str):
        """Logging"""
        self.log_fn(message)

    def render_tab(self):
        """Render tab into UI"""
        with gr.Tab("Upscale Frames"):
            gr.HTML(SimpleIcons.INCREASING + "Use Real-ESRGAN to Enlarge and Denoise Frames",
                elem_id="tabheading")
            with gr.Row():
                with gr.Column():
                    input_path_text = gr.Text(max_lines=1,
                        placeholder="Path on this server to the frame PNG files",
                        label="Input Path")
                    output_path_text = gr.Text(max_lines=1,
                    placeholder="Where to place the upscaled frames, leave blank to use default",
                        label="Output Path")
                    with gr.Row():
                        scale_input = gr.Slider(value=4.0, minimum=1.0, maximum=8.0, step=0.05,
                            label="Frame Upscale Factor")
            upscale_button = gr.Button("Upscale Frames", variant="primary")
            with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Guide", open=False):
                WebuiTips.upscale_frames.render()
        upscale_button.click(self.upscale_frames,
            inputs=[input_path_text, output_path_text, scale_input])

    def upscale_frames(self, input_path : str, output_path : str | None, upscale_factor : float):
        """Upscale Frames button handler"""
        if input_path:
            model_name = self.config.realesrgan_settings["model_name"]
            gpu_ips = self.config.gpu_ids
            fp32 = self.config.realesrgan_settings["fp32"]
            upscaler = UpscaleSeries(model_name, gpu_ips, fp32, self.log)
            if output_path:
                create_directory(output_path)
            else:
                base_output_path = self.config.directories["output_upscaling"]
                output_path, _ = AutoIncrementDirectory(base_output_path).next_directory("run")
            output_basename = "upscaled_frames"
            file_list = get_files(input_path, extension="png")
            self.log(f"beginning series of upscaling at {output_path}")
            upscaler.upscale_series(file_list, output_path, upscale_factor, output_basename)
