import os
import shutil
from typing import Callable
import gradio as gr
from webui_utils.simple_config import SimpleConfig
from webui_utils.simple_icons import SimpleIcons
from webui_utils.image_utils import create_gif
from webui_utils.file_utils import get_files, create_directory, locate_frame_file
from webui_tips import WebuiTips
from interpolate_engine import InterpolateEngine
from interpolate import Interpolate
from interpolation_target import TargetInterpolate
from restore_frames import RestoreFrames
from webui_utils.auto_increment import AutoIncrementDirectory, AutoIncrementFilename
from video_blender import VideoBlenderState, VideoBlenderProjects
from webui_utils.video_utils import PNGtoMP4, QUALITY_SMALLER_SIZE

class VideoBlender():
    def __init__(self,
                    config : SimpleConfig,
                    engine : InterpolateEngine,
                    log_fn : Callable):
        self.engine = engine
        self.config = config
        self.log_fn = log_fn
        self.video_blender_state = None
        self.video_blender_projects = VideoBlenderProjects(self.config.blender_settings["projects_file"])

    def log(self, message : str):
        self.log_fn(message)

    def render_tab(self):
        skip_frames = self.config.blender_settings['skip_frames']
        frame_rate = self.config.png_to_mp4_settings["frame_rate"]
        e = {}
        with gr.Tab("Video Blender"):
            gr.HTML(SimpleIcons.MICROSCOPE + "Combine original and replacement frames to manually restore a video", elem_id="tabheading")
            with gr.Tabs() as e["tabs_video_blender"]:

                ### PROJECT SETTINGS
                with gr.Tab(SimpleIcons.NOTEBOOK + "Project Settings", id=0):
                    with gr.Row():
                        e["input_project_name_vb"] = gr.Textbox(label="Project Name")
                        e["projects_dropdown_vb"] = gr.Dropdown(label=SimpleIcons.PROP_SYMBOL + " Saved Projects", choices=self.video_blender_projects.get_project_names())
                        e["load_project_button_vb"] = gr.Button(SimpleIcons.PROP_SYMBOL + " Load").style(full_width=False)
                        e["save_project_button_vb"] = gr.Button(SimpleIcons.PROP_SYMBOL + " Save").style(full_width=False)
                    with gr.Row():
                        e["input_project_path_vb"] = gr.Textbox(label="Project Frames Path", placeholder="Path to frame PNG files for video being restored")
                    with gr.Row():
                        e["input_path1_vb"] = gr.Textbox(label="Original / Video #1 Frames Path", placeholder="Path to original or video #1 PNG files")
                    with gr.Row():
                        e["input_path2_vb"] = gr.Textbox(label="Alternate / Video #2 Frames Path", placeholder="Path to alternate or video #2 PNG files")
                    e["load_button_vb"] = gr.Button("Open Video Blender Project " + SimpleIcons.ROCKET, variant="primary")
                    with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Guide", open=False):
                        WebuiTips.video_blender_project_settings.render()

                ### FRAME CHOOSER
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
                                e["input_text_frame_vb"] = gr.Number(value=0, precision=0, label="Frame Number")
                            with gr.Row():
                                e["prev_xframes_button_vb"] = gr.Button(f"<< {skip_frames}")
                                e["next_xframes_button_vb"] = gr.Button(f"{skip_frames} >>")
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

                    with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Guide", open=False):
                        WebuiTips.video_blender_frame_chooser.render()

                ### FRAME FIXER
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
                            e["preview_image_ff"] = gr.Image(type="filepath", label="Fixed Frames Preview", interactive=False, elem_id="mainoutput")
                            e["fixed_path_ff"] = gr.Text(label="Path to Restored Frames", interactive=False)
                            e["use_fixed_button_ff"] = gr.Button(value="Apply Fixed Frames", elem_id="actionbutton")
                    with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Guide", open=False):
                        WebuiTips.video_blender_frame_fixer.render()

                ### VIDEO PREVIEW
                with gr.Tab(SimpleIcons.TELEVISION + "Video Preview", id=3):
                    with gr.Row():
                        e["video_preview_vb"] = gr.Video(label="Preview", interactive=False, include_audio=False)
                    e["preview_path_vb"] = gr.Textbox(max_lines=1, label="Path to PNG Sequence", placeholder="Path on this server to the PNG files to be converted")
                    with gr.Row():
                        e["render_video_vb"] = gr.Button("Render Video", variant="primary")
                        e["input_frame_rate_vb"] = gr.Slider(minimum=1, maximum=60, value=frame_rate, step=1, label="Frame Rate")
                    with gr.Accordion(SimpleIcons.TIPS_SYMBOL + " Guide", open=False):
                        WebuiTips.video_blender_video_preview.render()

        e["load_project_button_vb"].click(self.video_blender_choose_project, inputs=[e["projects_dropdown_vb"]], outputs=[e["input_project_name_vb"], e["input_project_path_vb"], e["input_path1_vb"], e["input_path2_vb"]], show_progress=False)
        e["save_project_button_vb"].click(self.video_blender_save_project, inputs=[e["input_project_name_vb"], e["input_project_path_vb"], e["input_path1_vb"], e["input_path2_vb"]], show_progress=False)
        e["load_button_vb"].click(self.video_blender_load, inputs=[e["input_project_path_vb"], e["input_path1_vb"], e["input_path2_vb"]], outputs=[e["tabs_video_blender"], e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["prev_frame_button_vb"].click(self.video_blender_prev_frame, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["next_frame_button_vb"].click(self.video_blender_next_frame, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["go_button_vb"].click(self.video_blender_goto_frame, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["input_text_frame_vb"].submit(self.video_blender_goto_frame, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["use_path_1_button_vb"].click(self.video_blender_use_path1, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["use_path_2_button_vb"].click(self.video_blender_use_path2, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["prev_xframes_button_vb"].click(self.video_blender_skip_prev, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["next_xframes_button_vb"].click(self.video_blender_skip_next, inputs=[e["input_text_frame_vb"]], outputs=[e["input_text_frame_vb"], e["output_img_path1_vb"], e["output_prev_frame_vb"], e["output_curr_frame_vb"], e["output_next_frame_vb"], e["output_img_path2_vb"]], show_progress=False)
        e["preview_video_vb"].click(self.video_blender_preview_video, inputs=e["input_project_path_vb"], outputs=[e["tabs_video_blender"], e["preview_path_vb"]])
        e["fix_frames_button_vb"].click(self.video_blender_fix_frames, inputs=[e["input_project_path_vb"], e["input_text_frame_vb"]], outputs=[e["tabs_video_blender"], e["project_path_ff"], e["input_clean_before_ff"], e["input_clean_after_ff"]])
        e["preview_button_ff"].click(self.video_blender_preview_fixed, inputs=[e["project_path_ff"], e["input_clean_before_ff"], e["input_clean_after_ff"]], outputs=[e["preview_image_ff"], e["fixed_path_ff"]])
        e["use_fixed_button_ff"].click(self.video_blender_used_fixed, inputs=[e["project_path_ff"], e["fixed_path_ff"], e["input_clean_before_ff"]], outputs=e["tabs_video_blender"])
        e["render_video_vb"].click(self.video_blender_render_preview, inputs=[e["preview_path_vb"], e["input_frame_rate_vb"]], outputs=[e["video_preview_vb"]])
        return e

    def video_blender_load(self, project_path, frames_path1, frames_path2):
        self.video_blender_state = VideoBlenderState(project_path, frames_path1, frames_path2)
        return gr.update(selected=1), 0, *self.video_blender_state.goto_frame(0)

    def video_blender_save_project(self, project_name : str, project_path : str, frames1_path : str, frames2_path : str):
        self.video_blender_projects.save_project(project_name, project_path, frames1_path, frames2_path)

    def video_blender_choose_project(self, project_name):
        if project_name:
            dictobj = self.video_blender_projects.load_project(project_name)
            if dictobj:
                return dictobj["project_name"], dictobj["project_path"], dictobj["frames1_path"], dictobj["frames2_path"]
        return

    def video_blender_prev_frame(self, frame : str):
        frame = int(frame)
        frame -= 1
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_next_frame(self, frame : str):
        frame = int(frame)
        frame += 1
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_goto_frame(self, frame : str):
        frame = int(frame)
        frame = 0 if frame < 0 else frame
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_skip_next(self, frame : str):
        frame = int(frame) + int(self.config.blender_settings["skip_frames"])
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_skip_prev(self, frame : str):
        frame = int(frame) - int(self.config.blender_settings["skip_frames"])
        frame = 0 if frame < 0 else frame
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_use_path1(self, frame : str):
        frame = int(frame)
        to_filepath = self.video_blender_state.get_frame_file(VideoBlenderState.PROJECT_PATH, frame)
        from_filepath = self.video_blender_state.get_frame_file(VideoBlenderState.FRAMES1_PATH, frame)
        self.log(f"copying {from_filepath} to {to_filepath}")
        shutil.copy(from_filepath, to_filepath)
        frame += 1
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_use_path2(self, frame : str):
        frame = int(frame)
        to_filepath = self.video_blender_state.get_frame_file(VideoBlenderState.PROJECT_PATH, frame)
        from_filepath = self.video_blender_state.get_frame_file(VideoBlenderState.FRAMES2_PATH, frame)
        self.log(f"copying {from_filepath} to {to_filepath}")
        shutil.copy(from_filepath, to_filepath)
        frame += 1
        return frame, *self.video_blender_state.goto_frame(frame)

    def video_blender_fix_frames(self, project_path : str, frame : float):
        return gr.update(selected=2), project_path, frame, frame

    def video_blender_preview_fixed(self, project_path : str, before_frame : int, after_frame : int):
        if project_path and after_frame > before_frame:
            interpolater = Interpolate(self.engine.model, self.log)
            target_interpolater = TargetInterpolate(interpolater, self.log)
            frame_restorer = RestoreFrames(target_interpolater, self.log)
            base_output_path = self.config.directories["output_blender"]
            create_directory(base_output_path)
            output_path, run_index = AutoIncrementDirectory(base_output_path).next_directory("run")
            output_basename = "fixed_frames"

            before_file = locate_frame_file(project_path, before_frame)
            after_file = locate_frame_file(project_path, after_frame)
            num_frames = (after_frame - before_frame) - 1
            search_depth = int(self.config.blender_settings["frame_fixer_depth"])

            self.log(f"beginning frame fixes at {output_path}")
            frame_restorer.restore_frames(before_file, after_file, num_frames, search_depth, output_path, output_basename)
            output_paths = frame_restorer.output_paths

            preview_gif = os.path.join(output_path, output_basename + str(run_index) + ".gif")
            self.log(f"creating preview file {preview_gif}")
            duration = self.config.blender_settings["gif_duration"] / len(output_paths)
            gif_paths = [before_file, *output_paths, after_file]
            create_gif(gif_paths, preview_gif, duration=duration)

            return gr.Image.update(value=preview_gif), gr.Text.update(value=output_path, visible=True)

    def video_blender_used_fixed(self, project_path : str, fixed_frames_path : str, before_frame : int):
        fixed_frames = sorted(get_files(fixed_frames_path, "png"))
        frame = before_frame + 1
        for file in fixed_frames:
            project_file = locate_frame_file(project_path, frame)
            self.log(f"copying {file} to {project_file}")
            shutil.copy(file, project_file)
            frame += 1
        return gr.update(selected=1)

    def video_blender_preview_video(self, input_path : str):
        return gr.update(selected=3), input_path

    def video_blender_render_preview(self, input_path : str, frame_rate : int):
        if input_path:
            output_filepath, run_index = AutoIncrementFilename(self.config.directories["working"], "mp4").next_filename("video_preview", "mp4")
            PNGtoMP4(input_path, "auto", int(frame_rate), output_filepath, crf=QUALITY_SMALLER_SIZE)
            return output_filepath
