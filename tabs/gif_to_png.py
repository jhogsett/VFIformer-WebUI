import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips

def gif_to_png_tab(config, webui_events, e):
    with gr.Tab(SimpleIcons.CONV_SYMBOL + "GIF to PNG Sequence"):
        gr.Markdown("Convert GIF to a PNG sequence")
        e["input_path_text_gp"] = gr.Text(max_lines=1, label="GIF File", placeholder="Path on this server to the GIF file to be converted")
        e["output_path_text_gp"] = gr.Text(max_lines=1, label="PNG Files Path", placeholder="Path on this server to a directory for the converted PNG files")
        with gr.Row():
            e["convert_button_gp"] = gr.Button("Convert", variant="primary")
            e["output_info_text_gp"] = gr.Textbox(label="Details", interactive=False)
        with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
            WebuiTips.gif_to_png.render()
    e["convert_button_gp"].click(webui_events.convert_gif_to_png, inputs=[e["input_path_text_gp"], e["output_path_text_gp"]], outputs=e["output_info_text_gp"])
    return e
