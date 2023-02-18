import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from webui_tips import WebuiTips

def video_blender_tab(config, webui_events, e):
    with gr.Tab("Video Blender"):
        gr.HTML(SimpleIcons.MICROSCOPE + "Combine original and replacement frames to manually restore a video", elem_id="tabheading")
        with gr.Tabs() as e["tabs_video_blender"]:

            ### PROJECT SETTINGS
            with gr.Tab(SimpleIcons.NOTEBOOK + "Project Settings", id=0):
                with gr.Row():
                    e["input_project_name_vb"] = gr.Textbox(label="Project Name")
                    e["projects_dropdown_vb"] = gr.Dropdown(label=SimpleIcons.PROP_SYMBOL + " Saved Projects", choices=webui_events.video_blender_projects.get_project_names())
                    e["load_project_button_vb"] = gr.Button(SimpleIcons.PROP_SYMBOL + " Load").style(full_width=False)
                    e["save_project_button_vb"] = gr.Button(SimpleIcons.PROP_SYMBOL + " Save").style(full_width=False)
                with gr.Row():
                    e["input_project_path_vb"] = gr.Textbox(label="Project Frames Path", placeholder="Path to frame PNG files for video being restored")
                with gr.Row():
                    e["input_path1_vb"] = gr.Textbox(label="Original / Video #1 Frames Path", placeholder="Path to original or video #1 PNG files")
                with gr.Row():
                    e["input_path2_vb"] = gr.Textbox(label="Alternate / Video #2 Frames Path", placeholder="Path to alternate or video #2 PNG files")
                e["load_button_vb"] = gr.Button("Open Video Blender Project " + SimpleIcons.ROCKET, variant="primary")
                with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
                    WebuiTips.video_blender_project_settings.render()

            ### PROJECT SETTINGS
            with gr.Tab(SimpleIcons.CONTROLS + "Frame Chooser", id=1):
                with gr.Row():
                    with gr.Column():
                        gr.Textbox(visible=False)
                    with gr.Column():
                        e["output_img_path1_vb"] = gr.Image(label="Original / Path 1 Frame", interactive=False, type="filepath")
                    with gr.Column():
                        gr.Textbox(visible=False)
                with gr.Row():
                    with gr.Column():
                        e["output_prev_frame_vb"] = gr.Image(label="Previous Frame", interactive=False, type="filepath", elem_id="sideimage")
                    with gr.Column():
                        e["output_curr_frame_vb"] = gr.Image(label="Current Frame", interactive=False, type="filepath", elem_id="mainimage")
                    with gr.Column():
                        e["output_next_frame_vb"] = gr.Image(label="Next Frame", interactive=False, type="filepath", elem_id="sideimage")
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            e["go_button_vb"] = gr.Button("Go").style(full_width=False)
                            e["input_text_frame_vb"] = gr.Number(value=0, precision=0, label="Frame")
                        with gr.Row():
                            e["prev_xframes_button_vb"] = gr.Button(f"<< {config.blender_settings['skip_frames']}")
                            e["next_xframes_button_vb"] = gr.Button(f"{config.blender_settings['skip_frames']} >>")
                        e["preview_video_vb"] = gr.Button("Preview Video")
                    with gr.Column():
                        e["output_img_path2_vb"] = gr.Image(label="Repair / Path 2 Frame", interactive=False, type="filepath")
                    with gr.Column():
                        e["use_path_1_button_vb"] = gr.Button("Use Path 1 Frame | Next >", variant="primary", elem_id="actionbutton")
                        e["use_path_2_button_vb"] = gr.Button("Use Path 2 Frame | Next >", variant="primary", elem_id="actionbutton")
                        with gr.Row():
                            e["prev_frame_button_vb"] = gr.Button("< Prev Frame", variant="primary")
                            e["next_frame_button_vb"] = gr.Button("Next Frame >", variant="primary")
                        e["fix_frames_button_vb"] = gr.Button("Fix Frames")

                with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
                    WebuiTips.video_blender_frame_chooser.render()

            ### PROJECT SETTINGS
            with gr.Tab(SimpleIcons.HAMMER + "Frame Fixer", id=2):
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            e["project_path_ff"] = gr.Text(label="Video Blender Project Path", placeholder="Path to video frame PNG files")
                        with gr.Row():
                            e["input_clean_before_ff"] = gr.Number(label="Last clean frame BEFORE damaged ones", value=0, precision=0)
                            e["input_clean_after_ff"] = gr.Number(label="First clean frame AFTER damaged ones", value=0, precision=0)
                        with gr.Row():
                            e["preview_button_ff"] = gr.Button(value="Preview Fixed Frames", variant="primary")
                    with gr.Column():
                        e["preview_image_ff"] = gr.Image(type="filepath", label="Fixed Frames Preview", interactive=False)
                        e["fixed_path_ff"] = gr.Text(label="Path to Restored Frames", interactive=False)
                        e["use_fixed_button_ff"] = gr.Button(value="Apply Fixed Frames", elem_id="actionbutton")
                with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
                    WebuiTips.video_blender_frame_fixer.render()

            ### VIDEO PREVIEW

            with gr.Tab(SimpleIcons.TELEVISION + "Video Preview", id=3):
                with gr.Row():
                    e["video_preview_vb"] = gr.Video(label="Preview", interactive=False, include_audio=False) #.style(width=config.blender_settings["preview_width"]) #height=config.blender_settings["preview_height"],
                e["preview_path_vb"] = gr.Textbox(max_lines=1, label="Path to PNG Sequence", placeholder="Path on this server to the PNG files to be converted")
                with gr.Row():
                    e["render_video_vb"] = gr.Button("Render Video", variant="primary")
                    e["input_frame_rate_vb"] = gr.Slider(minimum=1, maximum=60, value=config.png_to_mp4_settings["frame_rate"], step=1, label="Frame Rate")
                with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Tips", open=False):
                    WebuiTips.video_blender_video_preview.render()
    e["load_project_button_vb"].click(webui_events.video_blender_choose_project, inputs=[e["projects_dropdown_vb"]], outputs=[e["input_project_name_vb"], e["input_project_path_vb"], e["input_path1_vb"], e["input_path2_vb"]], show_progress=False)
    e["save_project_button_vb"].click(webui_events.video_blender_save_project, inputs=[e["input_project_name_vb"], e["input_project_path_vb"], e["input_path1_vb"], e["input_path2_vb"]], show_progress=False)
    e["load_button_vb"].click(webui_events.video_blender_load, inputs=[e["input_project_path_vb"], e["input_path1_vb"], e["input_path2_vb"]], outputs=[e["tabs_video_blender"], e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
    e["prev_frame_button_vb"].click(webui_events.video_blender_prev_frame, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
    e["next_frame_button_vb"].click(webui_events.video_blender_next_frame, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
    e["go_button_vb"].click(webui_events.video_blender_goto_frame, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
    e["input_text_frame_vb"].submit(webui_events.video_blender_goto_frame, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
    e["use_path_1_button_vb"].click(webui_events.video_blender_use_path1, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
    e["use_path_2_button_vb"].click(webui_events.video_blender_use_path2, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
    e["prev_xframes_button_vb"].click(webui_events.video_blender_skip_prev, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
    e["next_xframes_button_vb"].click(webui_events.video_blender_skip_next, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
    e["preview_video_vb"].click(webui_events.video_blender_preview_video, inputs=e["input_project_path_vb"], outputs=[e["tabs_video_blender"], e["preview_path_vb"]])
    e["fix_frames_button_vb"].click(webui_events.video_blender_fix_frames, inputs=[e["input_project_path_vb"], e["input_text_frame_vb"]], outputs=[e["tabs_video_blender"], e["project_path_ff"], e["input_clean_before_ff"], e["input_clean_after_ff"]])
    e["preview_button_ff"].click(webui_events.video_blender_preview_fixed, inputs=[e["project_path_ff"], e["input_clean_before_ff"], e["input_clean_after_ff"]], outputs=[e["preview_image_ff"], e["fixed_path_ff"]])
    e["use_fixed_button_ff"].click(webui_events.video_blender_used_fixed, inputs=[e["project_path_ff"], e["fixed_path_ff"], e["input_clean_before_ff"]], outputs=e["tabs_video_blender"])
    e["render_video_vb"].click(webui_events.video_blender_render_preview, inputs=[e["preview_path_vb"], e["input_frame_rate_vb"]], outputs=[e["video_preview_vb"]])
    return e
