import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips

def frame_interpolation_tab(config, webui_events, e):
    with gr.Tab("Frame Interpolation"):
        gr.HTML(SimpleIcons.DIVIDE + "Divide the time between two frames to any depth, see an animation of result and download the new frames", elem_id="tabheading")
        with gr.Row():
            with gr.Column():
                e["img1_input_fi"] = gr.Image(type="filepath", label="Before Frame", tool=None)
                e["img2_input_fi"] = gr.Image(type="filepath", label="After Frame", tool=None)
                with gr.Row():
                    e["splits_input_fi"] = gr.Slider(value=1, minimum=1, maximum=config.interpolation_settings["max_splits"], step=1, label="Split Count")
                    e["info_output_fi"] = gr.Textbox(value="1", label="Interpolated Frames", max_lines=1, interactive=False)
            with gr.Column():
                e["img_output_fi"] = gr.Image(type="filepath", label="Animated Preview", interactive=False)
                e["file_output_fi"] = gr.File(type="file", file_count="multiple", label="Download", visible=False)
        e["interpolate_button_fi"] = gr.Button("Interpolate", variant="primary")
        with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
            WebuiTips.frame_interpolation.render()

    e["interpolate_button_fi"].click(webui_events.frame_interpolation, inputs=[e["img1_input_fi"], e["img2_input_fi"], e["splits_input_fi"]], outputs=[e["img_output_fi"], e["file_output_fi"]])
    e["splits_input_fi"].change(webui_events.update_splits_info, inputs=e["splits_input_fi"], outputs=e["info_output_fi"], show_progress=False)
    return e
