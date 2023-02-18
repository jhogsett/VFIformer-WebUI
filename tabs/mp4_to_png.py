import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips

def mp4_to_png_tab(config, webui_events, e):
    with gr.Tab(SimpleIcons.CONV_SYMBOL + "MP4 to PNG Sequence"):
        gr.Markdown("Convert MP4 to a PNG sequence")
        e["input_path_text_mp"] = gr.Text(max_lines=1, label="MP4 File", placeholder="Path on this server to the MP4 file to be converted")
        e["output_path_text_mp"] = gr.Text(max_lines=1, label="PNG Files Path", placeholder="Path on this server to a directory for the converted PNG files")
        with gr.Row():
            e["output_pattern_text_mp"] = gr.Text(max_lines=1, label="Output Filename Pattern", placeholder="Pattern like image%03d.png")
            e["input_frame_rate_mp"] = gr.Slider(minimum=1, maximum=60, value=config.mp4_to_png_settings["frame_rate"], step=1, label="Frame Rate")
        with gr.Row():
            e["convert_button_mp"] = gr.Button("Convert", variant="primary")
            e["output_info_text_mp"] = gr.Textbox(label="Details", interactive=False)
        with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
            WebuiTips.mp4_to_png.render()
    e["convert_button_mp"].click(webui_events.convert_mp4_to_png, inputs=[e["input_path_text_mp"], e["output_pattern_text_mp"], e["input_frame_rate_mp"], e["output_path_text_mp"]], outputs=e["output_info_text_mp"])
    return e
