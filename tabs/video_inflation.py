import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips

def video_inflation_tab(config, webui_events, e):
    with gr.Tab("Video Inflation"):
        gr.HTML(SimpleIcons.BALLOON + "Double the number of video frames to any depth for super slow motion", elem_id="tabheading")
        with gr.Row():
            with gr.Column():
                e["input_path_text_vi"] = gr.Text(max_lines=1, placeholder="Path on this server to the frame PNG files", label="Input Path")
                e["output_path_text_vi"] = gr.Text(max_lines=1, placeholder="Where to place the generated frames, leave blank to use default", label="Output Path")
                with gr.Row():
                    e["splits_input_vi"] = gr.Slider(value=1, minimum=1, maximum=10, step=1, label="Splits")
                    e["info_output_vi"] = gr.Textbox(value="1", label="Interpolations per Frame", max_lines=1, interactive=False)
        gr.Markdown("*Progress can be tracked in the console*")
        e["interpolate_button_vi"] = gr.Button("Interpolate Series " + SimpleIcons.SLOW_SYMBOL, variant="primary")
        with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
            WebuiTips.video_inflation.render()
    e["interpolate_button_vi"].click(webui_events.video_inflation, inputs=[e["input_path_text_vi"], e["output_path_text_vi"], e["splits_input_vi"]])
    e["splits_input_vi"].change(webui_events.update_splits_info, inputs=e["splits_input_vi"], outputs=e["info_output_vi"], show_progress=False)
    return e
