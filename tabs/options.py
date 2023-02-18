import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips

def options_tab(config, webui_events, e, restart_fn):
    with gr.Tab(SimpleIcons.GEAR + "Options"):
        with gr.Row():
            e["restart_button"] = gr.Button("Restart App", variant="primary").style(full_width=False)
    e["restart_button"].click(restart_fn, _js="function(){setTimeout(function(){window.location.reload()},2000);return[]}")
    return e
