import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips

def png_to_mp4_tab(config, webui_events, e):
    with gr.Tab(SimpleIcons.CONV_SYMBOL + "PNG Sequence to MP4"):
        gr.Markdown("Convert a PNG sequence to a MP4")
        e["input_path_text_pm"] = gr.Text(max_lines=1, label="PNG Files Path", placeholder="Path on this server to the PNG files to be converted")
        e["output_path_text_pm"] = gr.Text(max_lines=1, label="MP4 File", placeholder="Path and filename on this server for the converted MP4 file")
        with gr.Row():
            e["input_pattern_text_pm"] = gr.Text(max_lines=1, label="Input Filename Pattern", placeholder="Pattern like image%03d.png (auto=automatic pattern)")
            e["input_frame_rate_pm"] = gr.Slider(minimum=1, maximum=60, value=config.png_to_mp4_settings["frame_rate"], step=1, label="Frame Rate")
            e["quality_slider_pm"] = gr.Slider(minimum=config.png_to_mp4_settings["minimum_crf"], maximum=config.png_to_mp4_settings["maximum_crf"], step=1, value=config.png_to_mp4_settings["default_crf"], label="Quality (lower=better)")
        with gr.Row():
            e["convert_button_pm"] = gr.Button("Convert", variant="primary")
            e["output_info_text_pm"] = gr.Textbox(label="Details", interactive=False)
        with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
            WebuiTips.png_to_mp4.render()
    e["convert_button_pm"].click(webui_events.convert_png_to_mp4, inputs=[e["input_path_text_pm"], e["input_pattern_text_pm"], e["input_frame_rate_pm"], e["output_path_text_pm"], e["quality_slider_pm"]], outputs=e["output_info_text_pm"])
    return e
