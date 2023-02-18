import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips

def png_to_gif_tab(config, webui_events, e):
    with gr.Tab(SimpleIcons.CONV_SYMBOL + "PNG Sequence to GIF"):
        gr.Markdown("Convert a PNG sequence to a GIF")
        e["input_path_text_pg"] = gr.Text(max_lines=1, label="PNG Files Path", placeholder="Path on this server to the PNG files to be converted")
        e["output_path_text_pg"] = gr.Text(max_lines=1, label="GIF File", placeholder="Path and filename on this server for the converted GIF file")
        e["input_pattern_text_pg"] = gr.Text(max_lines=1, label="Input Filename Pattern", placeholder="Pattern like image%03d.png (auto=automatic pattern)")
        with gr.Row():
            e["convert_button_pg"] = gr.Button("Convert", variant="primary")
            e["output_info_text_pg"] = gr.Textbox(label="Details", interactive=False)
        with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
            WebuiTips.png_to_gif.render()
    e["convert_button_pg"].click(webui_events.convert_png_to_gif, inputs=[e["input_path_text_pg"], e["input_pattern_text_pg"], e["output_path_text_pg"]], outputs=e["output_info_text_pg"])
    return e
