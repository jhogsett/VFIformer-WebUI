from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips
from interpolate_engine import InterpolateEngine
from resequence_files import ResequenceFiles as _ResequenceFiles

class ResequenceFiles():
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
        with gr.Tab(SimpleIcons.NUMBERS + "Resequence Files "):
            gr.HTML("Rename a PNG sequence for import into video editing software", elem_id="tabheading")
            with gr.Row():
                with gr.Column():
                    e["input_path_text2"] = gr.Text(max_lines=1, placeholder="Path on this server to the files to be resequenced", label="Input Path")
                    with gr.Row():
                        e["input_filetype_text"] = gr.Text(value="png", max_lines=1, placeholder="File type such as png", label="File Type")
                        e["input_newname_text"] = gr.Text(value="pngsequence", max_lines=1, placeholder="Base filename for the resequenced files", label="Base Filename")
                    with gr.Row():
                        e["input_start_text"] = gr.Text(value="0", max_lines=1, placeholder="Starting integer for the sequence", label="Starting Sequence Number")
                        e["input_step_text"] = gr.Text(value="1", max_lines=1, placeholder="Integer tep for the sequentially numbered files", label="Integer Step")
                        e["input_zerofill_text"] = gr.Text(value="-1", max_lines=1, placeholder="Padding with for sequential numbers, -1=auto", label="Number Padding")
                    with gr.Row():
                        e["input_rename_check"] = gr.Checkbox(value=False, label="Rename instead of duplicate files")
                    e["resequence_button"] = gr.Button("Resequence Files", variant="primary")
            with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
                WebuiTips.resequence_files.render()
        e["resequence_button"].click(self.resequence_files, inputs=[e["input_path_text2"], e["input_filetype_text"], e["input_newname_text"], e["input_start_text"], e["input_step_text"], e["input_zerofill_text"], e["input_rename_check"]])
        return e

    def resequence_files(self, input_path : str, input_filetype : str, input_newname : str, input_start : str, input_step : str, input_zerofill : str, input_rename_check : bool):
        if input_path and input_filetype and input_newname and input_start and input_step and input_zerofill:
            _ResequenceFiles(input_path, input_filetype, input_newname, int(input_start), int(input_step), int(input_zerofill), input_rename_check, self.log).resequence()
