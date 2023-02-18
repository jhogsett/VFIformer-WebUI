import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips

def frame_search_tab(config, webui_events, e):
    with gr.Tab("Frame Search"):
        gr.HTML(SimpleIcons.MAGNIFIER + "Search for an arbitrarily precise timed frame and return the closest match", elem_id="tabheading")
        with gr.Row():
            with gr.Column():
                e["img1_input_fs"] = gr.Image(type="filepath", label="Before Frame", tool=None)
                e["img2_input_fs"] = gr.Image(type="filepath", label="After Frame", tool=None)
                with gr.Row():
                    e["splits_input_fs"] = gr.Slider(value=1, minimum=1, maximum=config.search_settings["max_splits"], step=1, label="Search Precision")
                    e["min_input_text_fs"] = gr.Text(placeholder="0.0-1.0", label="Lower Bound")
                    e["max_input_text_fs"] = gr.Text(placeholder="0.0-1.0", label="Upper Bound")
            with gr.Column():
                e["img_output_fs"] = gr.Image(type="filepath", label="Found Frame", interactive=False)
                e["file_output_fs"] = gr.File(type="file", file_count="multiple", label="Download", visible=False)
        e["search_button_fs"] = gr.Button("Search", variant="primary")
        with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
            WebuiTips.frame_search.render()
    e["search_button_fs"].click(webui_events.frame_search, inputs=[e["img1_input_fs"], e["img2_input_fs"], e["splits_input_fs"], e["min_input_text_fs"], e["max_input_text_fs"]], outputs=[e["img_output_fs"], e["file_output_fs"]])
    return e
