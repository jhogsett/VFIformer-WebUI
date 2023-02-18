import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips
from webui_utils.simple_utils import restored_frame_fractions, restored_frame_predictions

def frame_restoration_tab(config, webui_events, e):
    with gr.Tab("Frame Restoration"):
        gr.HTML(SimpleIcons.MAGIC_WAND + "Restore multiple adjacent bad frames using precision interpolation", elem_id="tabheading")
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    e["img1_input_fr"] = gr.Image(type="filepath", label="Frame Before Replacement Frames", tool=None)
                    e["img2_input_fr"] = gr.Image(type="filepath", label="Frame After Replacement Frames", tool=None)
                with gr.Row():
                    e["frames_input_fr"] = gr.Slider(value=config.restoration_settings["default_frames"], minimum=1, maximum=config.restoration_settings["max_frames"], step=1, label="Frames to Restore")
                    e["precision_input_fr"] = gr.Slider(value=config.restoration_settings["default_precision"], minimum=1, maximum=config.restoration_settings["max_precision"], step=1, label="Search Precision")
                with gr.Row():
                    times_default = restored_frame_fractions(config.restoration_settings["default_frames"])
                    e["times_output_fr"] = gr.Textbox(value=times_default, label="Frame Search Times", max_lines=1, interactive=False)
            with gr.Column():
                e["img_output_fr"] = gr.Image(type="filepath", label="Animated Preview", interactive=False)
                e["file_output_fr"] = gr.File(type="file", file_count="multiple", label="Download", visible=False)
        predictions_default = restored_frame_predictions(config.restoration_settings["default_frames"], config.restoration_settings["default_precision"])
        e["predictions_output_fr"] = gr.Textbox(value=predictions_default, label="Predicted Matches", max_lines=1, interactive=False)
        e["restore_button_fr"] = gr.Button("Restore Frames", variant="primary")
        with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
            WebuiTips.frame_restoration.render()
    e["restore_button_fr"].click(webui_events.frame_restoration, inputs=[e["img1_input_fr"], e["img2_input_fr"], e["frames_input_fr"], e["precision_input_fr"]], outputs=[e["img_output_fr"], e["file_output_fr"]])
    e["frames_input_fr"].change(webui_events.update_info_fr, inputs=[e["frames_input_fr"], e["precision_input_fr"]], outputs=[e["times_output_fr"], e["predictions_output_fr"]], show_progress=False)
    e["precision_input_fr"].change(webui_events.update_info_fr, inputs=[e["frames_input_fr"], e["precision_input_fr"]], outputs=[e["times_output_fr"], e["predictions_output_fr"]], show_progress=False)
    return e
