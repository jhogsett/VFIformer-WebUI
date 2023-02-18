import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips

def future_tab(config, webui_events, e):
    with gr.Tab(SimpleIcons.WISH_SYMBOL + "GIF to Video"):
        with gr.Row():
            with gr.Column():
                WebuiTips.gif_to_mp4.render()

    with gr.Tab(SimpleIcons.WISH_SYMBOL + "Upscaling"):
        WebuiTips.upscaling.render()
    return e
