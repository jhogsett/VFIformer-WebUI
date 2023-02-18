import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips
from webui_utils.simple_utils import fps_change_details

def change_fps_tab(config, webui_events, e):
    with gr.Tab(SimpleIcons.FILM + "Change FPS"):
        gr.HTML("Change the frame rate for a set of PNG video frames using frame search", elem_id="tabheading")
        max_fps = config.fps_change_settings["maximum_fps"]
        starting_fps = config.fps_change_settings["starting_fps"]
        ending_fps = config.fps_change_settings["ending_fps"]
        max_precision = config.fps_change_settings["max_precision"]
        precision = config.fps_change_settings["default_precision"]
        lowest_common_rate, filled, sampled, fractions, predictions = fps_change_details(starting_fps, ending_fps, precision)
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    e["input_path_text_fc"] = gr.Text(max_lines=1, label="Input Path", placeholder="Path on this server to the PNG frame files to be converted")
                    e["output_path_text_fc"] = gr.Text(max_lines=1, label="Output Path", placeholder="Path on this server for the converted PNG frame files, leave blank to use default")
                with gr.Row():
                    e["starting_fps_fc"] = gr.Slider(value=starting_fps, minimum=1, maximum=max_fps, step=1, label="Starting FPS")
                    e["ending_fps_fc"] = gr.Slider(value=ending_fps, minimum=1, maximum=max_fps, step=1, label="Ending FPS")
                    e["output_lcm_text_fc"] = gr.Text(value=lowest_common_rate, max_lines=1, label="Lowest Common FPS", interactive=False)
                    e["output_filler_text_fc"] = gr.Text(value=filled, max_lines=1, label="Filled Frames per Input Frame", interactive=False)
                    e["output_sampled_text_fc"] = gr.Text(value=sampled, max_lines=1, label="Output Frames Sample Rate", interactive=False)
                with gr.Row():
                    e["precision_fc"] = gr.Slider(value=precision, minimum=1, maximum=max_precision, step=1, label="Precision")
                    e["times_output_fc"] = gr.Textbox(value=fractions, label="Frame Search Times", max_lines=8, interactive=False)
                    e["predictions_output_fc"] = gr.Textbox(value=predictions, label="Predicted Matches", max_lines=8, interactive=False)
        gr.Markdown("*Progress can be tracked in the console*")
        e["convert_button_fc"] = gr.Button("Convert " + SimpleIcons.SLOW_SYMBOL, variant="primary")
        with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
            WebuiTips.change_fps.render()
    e["starting_fps_fc"].change(webui_events.update_info_fc, inputs=[e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]], outputs=[e["output_lcm_text_fc"], e["output_filler_text_fc"], e["output_sampled_text_fc"], e["times_output_fc"], e["predictions_output_fc"]], show_progress=False)
    e["ending_fps_fc"].change(webui_events.update_info_fc, inputs=[e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]], outputs=[e["output_lcm_text_fc"], e["output_filler_text_fc"], e["output_sampled_text_fc"], e["times_output_fc"], e["predictions_output_fc"]], show_progress=False)
    e["precision_fc"].change(webui_events.update_info_fc, inputs=[e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]], outputs=[e["output_lcm_text_fc"], e["output_filler_text_fc"], e["output_sampled_text_fc"], e["times_output_fc"], e["predictions_output_fc"]], show_progress=False)
    e["convert_button_fc"].click(webui_events.convert_fc, inputs=[e["input_path_text_fc"], e["output_path_text_fc"], e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]])
    return e
