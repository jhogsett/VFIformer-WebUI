import os
import time
import signal
import argparse
import gradio as gr
from interpolate_engine import InterpolateEngine
from webui_utils.simple_log import SimpleLog
from webui_utils.simple_config import SimpleConfig
from webui_utils.file_utils import create_directories
from create_ui import create_ui
from resample_series import ResampleSeries
from webui_events import WebuiEvents

log = None
config = None
engine= None
restart = False
prevent_inbrowser = False

def main():
    global log, config, engine, prevent_inbrowser, video_blender_projects
    parser = argparse.ArgumentParser(description='VFIformer Web UI')
    parser.add_argument("--config_path", type=str, default="config.yaml", help="path to config YAML file")
    parser.add_argument("--verbose", dest="verbose", default=False, action="store_true", help="Show extra details")
    args = parser.parse_args()

    log = SimpleLog(args.verbose)
    config = SimpleConfig(args.config_path).config_obj()
    create_directories(config.directories)
    engine = InterpolateEngine(config.model, config.gpu_ids)
    webui_events = WebuiEvents(engine, config, log)

    while True:
        print("Starting VFIformer-WebUI")
        print("Please be patient, the models are loaded on the first interpolation")

        app = setup_ui(config, webui_events)
        app.launch(inbrowser = config.auto_launch_browser and not prevent_inbrowser,
                    server_name = config.server_name,
                    server_port = config.server_port,
                    prevent_thread_lock=True)

        # idea borrowed from stable-diffusion-webui webui.py
        # after initial launch, disable inbrowser for subsequent restarts
        prevent_inbrowser = True

        wait_on_server(app)
        print("\n--- Restarting\n")

def restart_app():
    global restart
    restart = True

#### Gradio UI

def setup_ui(config, webui_events):
    with gr.Blocks(analytics_enabled=False,
                    title="VFIformer Web UI",
                    theme=config.user_interface["theme"],
                    css=config.user_interface["css_file"]) as app:
        e = create_ui(config, webui_events.video_blender_projects)

        # bind UI elemements to event handlers
        e["interpolate_button_fi"].click(webui_events.frame_interpolation, inputs=[e["img1_input_fi"], e["img2_input_fi"], e["splits_input_fi"]], outputs=[e["img_output_fi"], e["file_output_fi"]])
        e["splits_input_fi"].change(webui_events.update_splits_info, inputs=e["splits_input_fi"], outputs=e["info_output_fi"], show_progress=False)
        e["search_button_fs"].click(webui_events.frame_search, inputs=[e["img1_input_fs"], e["img2_input_fs"], e["splits_input_fs"], e["min_input_text_fs"], e["max_input_text_fs"]], outputs=[e["img_output_fs"], e["file_output_fs"]])
        e["interpolate_button_vi"].click(webui_events.video_inflation, inputs=[e["input_path_text_vi"], e["output_path_text_vi"], e["splits_input_vi"]])
        e["splits_input_vi"].change(webui_events.update_splits_info, inputs=e["splits_input_vi"], outputs=e["info_output_vi"], show_progress=False)
        e["resynthesize_button_rv"].click(webui_events.resynthesize_video, inputs=[e["input_path_text_rv"], e["output_path_text_rv"]])
        e["restore_button_fr"].click(webui_events.frame_restoration, inputs=[e["img1_input_fr"], e["img2_input_fr"], e["frames_input_fr"], e["precision_input_fr"]], outputs=[e["img_output_fr"], e["file_output_fr"]])
        e["frames_input_fr"].change(webui_events.update_info_fr, inputs=[e["frames_input_fr"], e["precision_input_fr"]], outputs=[e["times_output_fr"], e["predictions_output_fr"]], show_progress=False)
        e["precision_input_fr"].change(webui_events.update_info_fr, inputs=[e["frames_input_fr"], e["precision_input_fr"]], outputs=[e["times_output_fr"], e["predictions_output_fr"]], show_progress=False)
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
        e["convert_button_mp"].click(webui_events.convert_mp4_to_png, inputs=[e["input_path_text_mp"], e["output_pattern_text_mp"], e["input_frame_rate_mp"], e["output_path_text_mp"]], outputs=e["output_info_text_mp"])
        e["convert_button_pm"].click(webui_events.convert_png_to_mp4, inputs=[e["input_path_text_pm"], e["input_pattern_text_pm"], e["input_frame_rate_pm"], e["output_path_text_pm"], e["quality_slider_pm"]], outputs=e["output_info_text_pm"])
        e["convert_button_gp"].click(webui_events.convert_gif_to_mp4, inputs=[e["input_path_text_gp"], e["output_path_text_gp"]], outputs=e["output_info_text_gp"])
        e["convert_button_pg"].click(webui_events.convert_png_to_gif, inputs=[e["input_path_text_pg"], e["input_pattern_text_pg"], e["output_path_text_pg"]], outputs=e["output_info_text_pg"])
        e["resequence_button"].click(webui_events.resequence_files, inputs=[e["input_path_text2"], e["input_filetype_text"], e["input_newname_text"], e["input_start_text"], e["input_step_text"], e["input_zerofill_text"], e["input_rename_check"]])
        e["starting_fps_fc"].change(webui_events.update_info_fc, inputs=[e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]], outputs=[e["output_lcm_text_fc"], e["output_filler_text_fc"], e["output_sampled_text_fc"], e["times_output_fc"], e["predictions_output_fc"]], show_progress=False)
        e["ending_fps_fc"].change(webui_events.update_info_fc, inputs=[e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]], outputs=[e["output_lcm_text_fc"], e["output_filler_text_fc"], e["output_sampled_text_fc"], e["times_output_fc"], e["predictions_output_fc"]], show_progress=False)
        e["precision_fc"].change(webui_events.update_info_fc, inputs=[e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]], outputs=[e["output_lcm_text_fc"], e["output_filler_text_fc"], e["output_sampled_text_fc"], e["times_output_fc"], e["predictions_output_fc"]], show_progress=False)
        e["convert_button_fc"].click(webui_events.convert_fc, inputs=[e["input_path_text_fc"], e["output_path_text_fc"], e["starting_fps_fc"], e["ending_fps_fc"], e["precision_fc"]])
        e["restart_button"].click(restart_app, _js="function(){setTimeout(function(){window.location.reload()},2000);return[]}")
    return app

#### code borrowed from stable-diffusion-webui webui.py:
def wait_on_server(app):
    global restart
    while True:
        time.sleep(0.5)
        if restart:
            restart = False
            time.sleep(0.5)
            app.close()
            time.sleep(0.5)
            break

# make the program just exit at ctrl+c without waiting for anything
def sigint_handler(sig, frame):
    print(f'Interrupted with signal {sig} in {frame}')
    os._exit(0)

signal.signal(signal.SIGINT, sigint_handler)

if __name__ == '__main__':
    main()
