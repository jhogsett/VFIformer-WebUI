import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips

def resynthesize_video_tab(config, webui_events, e):
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
    e["resynthesize_button_rv"].click(webui_events.resynthesize_video, inputs=[e["input_path_text_rv"], e["output_path_text_rv"]])
    return e
