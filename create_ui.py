import gradio as gr
from webui_utils.simple_utils import restored_frame_fractions, restored_frame_predictions

def create_ui(config, video_blender_projects):
    gr.HTML("VFIformer Web UI", elem_id="appheading")

    with gr.Tab("Frame Interpolation"):
        gr.HTML("Divide the time between two frames to any depth, see an animation of result and download the new frames", elem_id="tabheading")
        with gr.Row(variant="compact"):
            with gr.Column(variant="panel"):
                img1_input_fi = gr.Image(type="filepath", label="Before Image", tool=None)
                img2_input_fi = gr.Image(type="filepath", label="After Image", tool=None)
                with gr.Row(variant="compact"):
                    splits_input_fi = gr.Slider(value=1, minimum=1, maximum=config.interpolation_settings["max_splits"], step=1, label="Splits")
                    info_output_fi = gr.Textbox(value="1", label="Interpolated Frames", max_lines=1, interactive=False)
            with gr.Column(variant="panel"):
                img_output_fi = gr.Image(type="filepath", label="Animated Preview", interactive=False)
                file_output_fi = gr.File(type="file", file_count="multiple", label="Download", visible=False)
        interpolate_button_fi = gr.Button("Interpolate", variant="primary")
        with gr.Accordion("Tips", open=False):
            gr.Markdown("""
            - Use this tool to reveal intricate details of the motion occurring between two video frames
            - Use it to quickly recreate a damaged frame
                - Set split count to _1_ and provide the _adjacent frames_
                - The _Frame Restoration_ tool can be used to recreate an arbitrary number of adjacent frames
            """)

    with gr.Tab("Frame Search"):
        gr.HTML("Search for an arbitrarily precise timed frame and return the closest match", elem_id="tabheading")
        with gr.Row(variant="compact"):
            with gr.Column(variant="panel"):
                img1_input_fs = gr.Image(type="filepath", label="Before Image", tool=None)
                img2_input_fs = gr.Image(type="filepath", label="After Image", tool=None)
                with gr.Row(variant="compact"):
                    splits_input_fs = gr.Slider(value=1, minimum=1, maximum=config.search_settings["max_splits"], step=1, label="Search Depth")
                    min_input_text_fs = gr.Text(placeholder="0.0-1.0", label="Lower Bound")
                    max_input_text_fs = gr.Text(placeholder="0.0-1.0", label="Upper Bound")
            with gr.Column(variant="panel"):
                img_output_fs = gr.Image(type="filepath", label="Found Frame", interactive=False)
                file_output_fs = gr.File(type="file", file_count="multiple", label="Download", visible=False)
        search_button_fs = gr.Button("Search", variant="primary")
        with gr.Accordion("Tips", open=False):
            gr.Markdown("""
            - Use this tool to synthesize a frame at an arbitrarily precise time using _Targeted Interpolation_
                - This is similar to a binary search:
                - The time interval between two frames is _halved_ recursively in the direction of the search target
                - New _between frames_ are interpolated at each step
                - A match is returned when a frame is found inside the search window, or if the search depth is reached
                - Search Depth should be set high if a precisely timed frame is needed
                - A low search depth may match a frame outside the search window""")

    with gr.Tab("Video Inflation"):
        gr.HTML("Double the number of video frames to any depth for super slow motion", elem_id="tabheading")
        with gr.Row(variant="compact"):
            with gr.Column(variant="panel"):
                input_path_text_vi = gr.Text(max_lines=1, placeholder="Path on this server to the frame PNG files", label="Input Path")
                output_path_text_vi = gr.Text(max_lines=1, placeholder="Where to place the generated frames, leave blank to use default", label="Output Path")
                with gr.Row(variant="compact"):
                    splits_input_vi = gr.Slider(value=1, minimum=1, maximum=10, step=1, label="Splits")
                    info_output_vi = gr.Textbox(value="1", label="Interpolations per Frame", max_lines=1, interactive=False)
        gr.Markdown("*Progress can be tracked in the console*")
        interpolate_button_vi = gr.Button("Interpolate Series (this will take time)", variant="primary")
        with gr.Accordion("Tips", open=False):
            gr.Markdown("""
            - This tool uses _Frame Interpolation_ on a sequence of video frame PNG files to double the frame count any number of times
            - This can have useful purposes:
                - Turn a regular video into a _super-slow-motion_ video
                - Expand the frames in a _time lapse_ video to _recover the original real-time video_
                - Create _smooth motion_ from otherwise _discrete motion_, like the second hand of a ticking clock

            # Important
            - This process will be slow, perhaps many hours long!
            - Progress will be shown in the console using a standard tqdm progress bar
            - The browser can be safely closed without interupting the process
            - There currently isn't an easy way to resume a halted inflation
                - A possible workaround:
                - Set aside the already-rendered frames from the input path
                - Re-run the inflation
                - Use the _Resequence Files_ tool to remix the two sets of rendered frames""")

    with gr.Tab("Resynthesize Video"):
        gr.HTML("Interpolate replacement frames from an entire video for use in movie restoration", elem_id="tabheading")
        with gr.Row(variant="compact"):
            with gr.Column(variant="panel"):
                input_path_text_rv = gr.Text(max_lines=1, placeholder="Path on this server to the frame PNG files", label="Input Path")
                output_path_text_rv = gr.Text(max_lines=1, placeholder="Where to place the generated frames, leave blank to use default", label="Output Path")
        gr.Markdown("*Progress can be tracked in the console*")
        resynthesize_button_rv = gr.Button("Resynthesize Video (this will take time)", variant="primary")
        with gr.Accordion("Tips", open=False):
            gr.Markdown("""
            - This tool creates a set of replacement frames for a video by interpolating new frames between all existing frames
                - For each replacement frame, the two adjacent original frames are used to interpolate a new _replacement frame_
                - Example:
                    - create a new frame #1 by interpolating a _between frame_ using original frames #0 and #2
                    - then create a new frame #2 using original frames #1 and #3
                    - then repeat this process for all frames in the original video
                - When done, there will be a complete set of synthesized replacement frames, matching frames in the original video, that can be used for movie restoration
                    - The _first_ and _last_ original frames cannot be resynthesized
            - How to use the replacement frames
                - The _Video Blender_ tool can be used to manually step through a video, easily replacing frames from a restoration set
            - Why this works
                - A video may have a single bad frame between two good frames
                - For example a bad splice, a video glitch, a double-exposed frame due to a mismatch in frame rates, etc.
                - VFIformer is excellent at detecting motion in all parts of a pair of frames, and will very accurately create a new clean replacement frame
            - When it doesn't work
                - It will not work to create replacement frames when there are not two adjacent CLEAN original frames
                - The _Frame Restoration_ tool can be used to recover an arbitrary number of adjacent damaged frames
                - It will not work to clean up transitions between scenes
                - If the motion between the two frames is too quick, it may not be detectable
                - Examples:
                    - An ax chopping wood may have moved too fast for any motion to be captured by the camera
                    - A first-person POV of a rollercoaster ride may have motion that's too different between frames to be detectable""")

    with gr.Tab("Frame Restoration"):
        gr.HTML("Restore multiple adjacent bad frames using precision interpolation", elem_id="tabheading")
        with gr.Row(variant="compact"):
            with gr.Column(variant="panel"):
                with gr.Row(variant="compact"):
                    img1_input_fr = gr.Image(type="filepath", label="Frame Before Replacement Frames", tool=None)
                    img2_input_fr = gr.Image(type="filepath", label="Frame After Replacement Frames", tool=None)
                with gr.Row(variant="compact"):
                    frames_input_fr = gr.Slider(value=config.restoration_settings["default_frames"], minimum=1, maximum=config.restoration_settings["max_frames"], step=1, label="Frames to Restore")
                    precision_input_fr = gr.Slider(value=config.restoration_settings["default_precision"], minimum=1, maximum=config.restoration_settings["max_precision"], step=1, label="Search Precision")
                with gr.Row(variant="compact"):
                    times_default = restored_frame_fractions(config.restoration_settings["default_frames"])
                    times_output_fr = gr.Textbox(value=times_default, label="Frame Search Times", max_lines=1, interactive=False)
            with gr.Column(variant="panel"):
                img_output_fr = gr.Image(type="filepath", label="Animated Preview", interactive=False)
                file_output_fr = gr.File(type="file", file_count="multiple", label="Download", visible=False)
        predictions_default = restored_frame_predictions(config.restoration_settings["default_frames"], config.restoration_settings["default_precision"])
        predictions_output_fr = gr.Textbox(value=predictions_default, label="Predicted Matches", max_lines=1, interactive=False)
        restore_button_fr = gr.Button("Restore Frames", variant="primary")
        with gr.Accordion("Tips", open=False):
            gr.Markdown("""
            - This tool uses _Frame Search_ to create restored frames for a series of adjacent bad frames
            - It can be used when basic _Frame Interpolation_ cannot due to the lack of adjacent clean frames
            - _Targeted Interpolation_ is used to search for replacement frames at precise times between the outer clean frames

            # Important
            - Provide only CLEAN frames adjacent to the series of bad frames
                - The frames should not cross scenes
                - Motion that is too fast may not produce good results
            - Set _Frames to Restore_ to the exact number of bad frames that need replacing to get accurate results
            - _Frame Search Times_ shows the fractional search times for the restored frames
                - Example with four frames:
                - If there are 2 bad frames b and c, and 2 good frames A and D:
                    - A---b---c---D
                    - Replacement frame B is 1/3 of the way between frames A and D
                    - Replacement frame C is 2/3 of the way between frames A and D
                    - _Targeted Interpolation_ can recreate frames at these precise times
            - Set _Search Precision_ to the _search depth_ needed for accuracy
                - Low _Search Precision_ is faster but can lead to repeated or poorly-timed frames
                - High _Search Precision_ takes longer but can produce near-perfect results
                - When restoring an even number of frames
                - When extreme accuracy is the goal
            - _Predicted Matches_ estimates the frame times that will be found based on _Frames to Restore_ and _Search Precision_
                - The actual found frames may differ from the predictions
                - A warning is displayed if _Search Precision_ should be increased because of possible repeated frames""")

    with gr.Tab("Video Blender"):
        gr.HTML("Combine original and replacement frames to manually restore a video", elem_id="tabheading")
        tabs_video_blender = gr.Tabs()
        with tabs_video_blender:
            with gr.Tab("Project Settings", id=0):
                with gr.Row():
                    input_project_name_vb = gr.Textbox(label="Project Name")
                    projects_dropdown_vb = gr.Dropdown(label="Saved Project Settings", choices=video_blender_projects.get_project_names())
                    load_project_button_vb = gr.Button("Load").style(full_width=False)
                    save_project_button_vb = gr.Button("Save").style(full_width=False)
                with gr.Row():
                    input_project_path_vb = gr.Textbox(label="Project Frames Path", placeholder="Path to frame PNG files for video being restored")
                with gr.Row():
                    input_path1_vb = gr.Textbox(label="Original / Video #1 Frames Path", placeholder="Path to original or video #1 PNG files")
                with gr.Row():
                    input_path2_vb = gr.Textbox(label="Alternate / Video #2 Frames Path", placeholder="Path to alternate or video #2 PNG files")
                load_button_vb = gr.Button("Open Video Blender Project", variant="primary")
                with gr.Accordion("Tips", open=False):
                    gr.Markdown("""
                    - Set up the project with three directories, all with PNG files (only) with the _same file count, dimensions and starting sequence number_
                    - The _Original / Video #1 Frames Path_ should have the _original PNG files_ from the video being restored
                    - The _Project Frames Path_ should start with a _copy of the original PNG files_ as a baseline set of frames
                    - The _Alternate / Video #2 Frames Path_ directory should have a set of _replacement PNG files_ used for restoration
                        - Replacement frames can be created using the _Resynthesize Video_ tool

                    # Important
                    - All paths must have the same number of files with _corresponding sequence numbers and dimensions_
                        - The _Resequence Files_ tool can be used to rename a set of PNG files
                        - If the _Resynthesize Video_ tool has been used, there will not be a resynthesized frame #0
                    - For _Video Preview_ to work properly:
                        - The files in each directory must have the _same base filename and numbering sequence_
                        - `ffmpeg.exe` must be available on the _system path_ to convert PNG frames for the preview video

                    # Project Management
                    - To save a settings for a project:
                        - After filling out all project text boxes, click _Save_
                        - A new row will be added to the projects file `./video_blender_projects.csv`
                        - To see the new project in the dropdown list:
                        - Restart the application via the Tools page, or from the console
                        - Reload the browser page and go back to the _Video Blender_ tab
                    - To load settings for a project
                        - Choose a project by name from the_Saved Project Settings_ DropDown
                        - Click _Load_
                        - Click _Open Video Blender Project_ to load the project and go to the _Frame Chooser_

                    General Use
                    - This tool can also be used any time there's a need to mix three videos, selectively replacing frames in one with frames from two others""")

            with gr.Tab("Frame Chooser", id=1):
                with gr.Row():
                    with gr.Column():
                        gr.Textbox(visible=False)
                    with gr.Column():
                        output_img_path1_vb = gr.Image(label="Original / Path 1 Frame", interactive=False, type="filepath")
                    with gr.Column():
                        gr.Textbox(visible=False)
                with gr.Row():
                    with gr.Column():
                        output_prev_frame_vb = gr.Image(label="Previous Frame", interactive=False, type="filepath", elem_id="sideimage")
                    with gr.Column():
                        output_curr_frame_vb = gr.Image(label="Current Frame", interactive=False, type="filepath", elem_id="mainimage")
                    with gr.Column():
                        output_next_frame_vb = gr.Image(label="Next Frame", interactive=False, type="filepath", elem_id="sideimage")
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            go_button_vb = gr.Button("Go").style(full_width=False)
                            input_text_frame_vb = gr.Number(value=0, precision=0, label="Frame")
                        with gr.Row():
                            prev_xframes_button_vb = gr.Button(f"<< {config.blender_settings['skip_frames']}")
                            next_xframes_button_vb = gr.Button(f"{config.blender_settings['skip_frames']} >>")
                        with gr.Row():
                            preview_video_vb = gr.Button("Preview Video")
                        use_back_button_vb = gr.Button("< Back", visible=False)
                    with gr.Column():
                        output_img_path2_vb = gr.Image(label="Repair / Path 2 Frame", interactive=False, type="filepath")
                    with gr.Column():
                        use_path_1_button_vb = gr.Button("Use Path 1 Frame | Next >", variant="primary", elem_id="redbutton")
                        use_path_2_button_vb = gr.Button("Use Path 2 Frame | Next >", variant="primary", elem_id="redbutton")
                        with gr.Row():
                            prev_frame_button_vb = gr.Button("< Prev Frame")
                            next_frame_button_vb = gr.Button("Next Frame >")
                with gr.Accordion("Tips", open=False):
                    gr.Markdown("""
                    # Important
                    - The red buttons copy files!
                        - They copy the corresponding frame PNG file from their respective directories to the project path
                        - The existing frame PNG file in the project path is overwritten
                        - The other buttons can be used without altering the project

                    Use the _Next Frame_ and _Prev Frame_ buttons to step through the video one frame at a time
                        - Tip: Press _Tab_ until the _Next Frame_ button is in focus, then use the SPACEBAR to step through the video

                    Clicking _Preview Video_ will take you to the _Preview Video_ tab
                        - The current set of project PNG frame files can be rendered into a video and watched""")

            with gr.Tab("Video Preview", id=2):
                with gr.Row():
                    video_preview_vb = gr.Video(label="Preview", interactive=False, include_audio=False) #.style(width=config.blender_settings["preview_width"]) #height=config.blender_settings["preview_height"],
                preview_path_vb = gr.Textbox(max_lines=1, label="Path to PNG Sequence", placeholder="Path on this server to the PNG files to be converted")
                with gr.Row():
                    render_video_vb = gr.Button("Render Video", variant="primary")
                    input_frame_rate_vb = gr.Slider(minimum=1, maximum=60, value=config.png_to_mp4_settings["frame_rate"], step=1, label="Frame Rate")
                with gr.Accordion("Tips", open=False):
                    gr.Markdown("""
                    - When coming to this tab from the _Frame Choose_ tab's _Preview Video_ button, the _Path to PNG Sequence_ is automatically filled with the Video Blender project path
                        - Simply click _Render Video_ to create and watch a preview of the project in its current state
                    - Preview videos are rendered in the directory set by the `directories:working` variable in `config.yaml`
                        - The directory is `./temp` by default and is not automatically purged

                    # Tip
                    - This tab can be used to render and watch a preview video for any directory of video frame PNG files
                    - Requirements:
                        - The files must be video frame PNG files with the same dimensions
                        - The filenames must all confirm to the same requirements:
                        - Have the same starting base filename
                        - Followed by a frame index integer, all zero-filled to the same width
                        - Example: `FRAME001.png` through `FRAME420.png`
                        - There must be no other PNG files in the same directory""")

    with gr.Tab("Tools"):
        with gr.Row(variant="compact"):
            restart_button = gr.Button("Restart App", variant="primary").style(full_width=False)

        with gr.Tab("Resequence Files"):
            gr.HTML("Rename a PNG sequence for import into video editing software", elem_id="tabheading")
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    input_path_text2 = gr.Text(max_lines=1, placeholder="Path on this server to the files to be resequenced", label="Input Path")
                    with gr.Row(variant="compact"):
                        input_filetype_text = gr.Text(value="png", max_lines=1, placeholder="File type such as png", label="File Type")
                        input_newname_text = gr.Text(value="pngsequence", max_lines=1, placeholder="Base filename for the resequenced files", label="Base Filename")
                    with gr.Row(variant="compact"):
                        input_start_text = gr.Text(value="0", max_lines=1, placeholder="Starting integer for the sequence", label="Starting Sequence Number")
                        input_step_text = gr.Text(value="1", max_lines=1, placeholder="Integer tep for the sequentially numbered files", label="Integer Step")
                        input_zerofill_text = gr.Text(value="-1", max_lines=1, placeholder="Padding with for sequential numbers, -1=auto", label="Number Padding")
                    with gr.Row(variant="compact"):
                        input_rename_check = gr.Checkbox(value=False, label="Rename instead of duplicate files")
                    resequence_button = gr.Button("Resequence Files", variant="primary")
            with gr.Accordion("Tips", open=False):
                gr.Markdown("""
                - The only PNG files present in the _Input Path_ should be the video frame files
                - _File Type_ is used for a wildcard search of files
                - _Base Filename_ is used to name the resequenced files with an added frame number
                - _Starting Sequence Number_ normally should be _0_
                    - A different value might be useful if inserting a PNG sequence into another
                - _Integer Step_ normally should be _1_
                    - This sets the increment between the added frame numbers
                - _Number Padding_ should be _-1_ for automatic detection
                    - It can be set to another value if a specific width of digits is needed for the frame number
                - Leave _Rename instead of duplicate files_ unchecked if the original files might be needed
                    - This can be helpful for tracing back to the source frame""")

        with gr.Tab("File Conversion"):
            gr.HTML("Tools for common video file conversion tasks (ffmpeg.exe must be in path)", elem_id="tabheading")

            with gr.Tab("MP4 to PNG Sequence"):
                gr.Markdown("Convert MP4 to a PNG sequence")
                input_path_text_mp = gr.Text(max_lines=1, label="MP4 File", placeholder="Path on this server to the MP4 file to be converted")
                output_path_text_mp = gr.Text(max_lines=1, label="PNG Files Path", placeholder="Path on this server to a directory for the converted PNG files")
                with gr.Row():
                    output_pattern_text_mp = gr.Text(max_lines=1, label="Output Filename Pattern", placeholder="Pattern like image%03d.png")
                    input_frame_rate_mp = gr.Slider(minimum=1, maximum=60, value=config.mp4_to_png_settings["frame_rate"], step=1, label="Frame Rate")
                convert_button_mp = gr.Button("Convert", variant="primary")
                output_info_text_mp = gr.Textbox(label="Details", interactive=False)
                with gr.Accordion("Tips", open=False):
                    gr.Markdown("""
                    - The filename pattern should be based on the count of frames  for alphanumeric sorting
                    - Example: For a video with _24,578_ frames and a PNG base filename of "TENNIS", the pattern should be "TENNIS%05d.png"
                    - Match the frame rate to the rate of the source video to avoid repeated or skipped frames
                    - The _Video Preview_ tab on the _Video Blender_ page can be used to watch a preview video of a set of PNG files""")

            with gr.Tab("PNG Sequence to MP4"):
                gr.Markdown("Convert a PNG sequence to a MP4")
                input_path_text_pm = gr.Text(max_lines=1, label="PNG Files Path", placeholder="Path on this server to the PNG files to be converted")
                output_path_text_pm = gr.Text(max_lines=1, label="MP4 File", placeholder="Path and filename on this server for the converted MP4 file")
                with gr.Row():
                    input_pattern_text_pm = gr.Text(max_lines=1, label="Input Filename Pattern", placeholder="Pattern like image%03d.png (auto=automatic pattern)")
                    input_frame_rate_pm = gr.Slider(minimum=1, maximum=60, value=config.png_to_mp4_settings["frame_rate"], step=1, label="Frame Rate")
                    quality_slider_pm = gr.Slider(minimum=config.png_to_mp4_settings["minimum_crf"], maximum=config.png_to_mp4_settings["maximum_crf"], step=1, value=config.png_to_mp4_settings["default_crf"], label="Quality (lower=better)")
                convert_button_pm = gr.Button("Convert", variant="primary")
                output_info_text_pm = gr.Textbox(label="Details", interactive=False)
                with gr.Accordion("Tips", open=False):
                    gr.Markdown("""
                    - The filename pattern should be based on the number of PNG files to ensure they're read in alphanumeric order
                    - Example: For a PNG sequence with _24,578_ files and filenames like "TENNIS24577.png", the pattern should be "TENNIS%05d.png"
                    - The special pattern "auto" can be used to detect the pattern automatically. This works when:
                        - The only PNG files present are the frame images
                        - All files have the same naming pattern, starting with a base filename, and the same width zero-filled frame number
                        - The first found PNG file follows the same naming pattern as all the other files
                    - The _Video Preview_ tab on the _Video Blender_ page can be used to watch a preview video of a set of PNG files""")

            with gr.Tab("GIF to PNG Sequence*"):
                gr.Markdown("*Planned: Convert a GIF to a PNG sequence")

            with gr.Tab("PNG Sequence to GIF*"):
                gr.Markdown("*Planned: Convert a PNG sequence to a GIF, specify duration and looping")

        with gr.Tab("Upscaling*"):
            gr.Markdown("*Planned: Use Real-ESRGAN 4x+ to restore and/or upscale images")

        with gr.Tab("GIF to Video*"):
            with gr.Row(variant="compact"):
                with gr.Column(variant="panel"):
                    gr.Markdown("""
                    *Idea: Recover the original video from animated GIF file
                    - split GIF into a series of PNG frames
                    - use R-ESRGAN 4x+ to restore and/or upscale
                    - use VFIformer to adjust frame rate to real time
                    - reassemble new PNG frames into MP4 file""")
    elements = {}
    elements["img1_input_fi"] = img1_input_fi
    elements["img2_input_fi"] = img2_input_fi
    elements["splits_input_fi"] = splits_input_fi
    elements["info_output_fi"] = info_output_fi
    elements["img_output_fi"] = img_output_fi
    elements["file_output_fi"] = file_output_fi
    elements["interpolate_button_fi"] = interpolate_button_fi
    elements["img1_input_fs"] = img1_input_fs
    elements["img2_input_fs"] = img2_input_fs
    elements["splits_input_fs"] = splits_input_fs
    elements["min_input_text_fs"] = min_input_text_fs
    elements["max_input_text_fs"] = max_input_text_fs
    elements["img_output_fs"] = img_output_fs
    elements["file_output_fs"] = file_output_fs
    elements["search_button_fs"] = search_button_fs
    elements["input_path_text_vi"] = input_path_text_vi
    elements["output_path_text_vi"] = output_path_text_vi
    elements["splits_input_vi"] = splits_input_vi
    elements["info_output_vi"] = info_output_vi
    elements["interpolate_button_vi"] = interpolate_button_vi
    elements["input_path_text_rv"] = input_path_text_rv
    elements["output_path_text_rv"] = output_path_text_rv
    elements["resynthesize_button_rv"] = resynthesize_button_rv
    elements["img1_input_fr"] = img1_input_fr
    elements["img2_input_fr"] = img2_input_fr
    elements["frames_input_fr"] = frames_input_fr
    elements["precision_input_fr"] = precision_input_fr
    elements["times_output_fr"] = times_output_fr
    elements["img_output_fr"] = img_output_fr
    elements["file_output_fr"] = file_output_fr
    elements["predictions_output_fr"] = predictions_output_fr
    elements["restore_button_fr"] = restore_button_fr
    elements["tabs_video_blender"] = tabs_video_blender
    elements["input_project_name_vb"] = input_project_name_vb
    elements["projects_dropdown_vb"] = projects_dropdown_vb
    elements["load_project_button_vb"] = load_project_button_vb
    elements["save_project_button_vb"] = save_project_button_vb
    elements["input_project_path_vb"] = input_project_path_vb
    elements["input_path1_vb"] = input_path1_vb
    elements["input_path2_vb"] = input_path2_vb
    elements["load_button_vb"] = load_button_vb
    elements["output_img_path1_vb"] = output_img_path1_vb
    elements["output_prev_frame_vb"] = output_prev_frame_vb
    elements["output_curr_frame_vb"] = output_curr_frame_vb
    elements["output_next_frame_vb"] = output_next_frame_vb
    elements["prev_frame_button_vb"] = prev_frame_button_vb
    elements["next_frame_button_vb"] = next_frame_button_vb
    elements["go_button_vb"] = go_button_vb
    elements["input_text_frame_vb"] = input_text_frame_vb ,
    elements["prev_xframes_button_vb"] = prev_xframes_button_vb
    elements["next_xframes_button_vb"] = next_xframes_button_vb
    elements["output_img_path2_vb"] = output_img_path2_vb
    elements["use_path_1_button_vb"] = use_path_1_button_vb
    elements["use_path_2_button_vb"] = use_path_2_button_vb
    elements["use_back_button_vb"] = use_back_button_vb
    elements["preview_video_vb"] = preview_video_vb
    elements["video_preview_vb"] = video_preview_vb
    elements["preview_path_vb"] = preview_path_vb
    elements["render_video_vb"] = render_video_vb
    elements["input_frame_rate_vb"] = input_frame_rate_vb
    elements["restart_button"] = restart_button
    elements["input_path_text2"] = input_path_text2
    elements["input_filetype_text"] = input_filetype_text
    elements["input_newname_text"] = input_newname_text
    elements["input_start_text"] = input_start_text
    elements["input_step_text"] = input_step_text
    elements["input_zerofill_text"] = input_zerofill_text
    elements["input_rename_check"] = input_rename_check
    elements["resequence_button"] = resequence_button
    elements["input_path_text_mp"] = input_path_text_mp
    elements["output_path_text_mp"] = output_path_text_mp
    elements["output_pattern_text_mp"] = output_pattern_text_mp
    elements["input_frame_rate_mp"] = input_frame_rate_mp
    elements["convert_button_mp"] = convert_button_mp
    elements["output_info_text_mp"] = output_info_text_mp
    elements["input_path_text_pm"] = input_path_text_pm
    elements["output_path_text_pm"] = output_path_text_pm
    elements["input_pattern_text_pm"] = input_pattern_text_pm
    elements["input_frame_rate_pm"] = input_frame_rate_pm
    elements["quality_slider_pm"] = quality_slider_pm
    elements["convert_button_pm"] = convert_button_pm
    elements["output_info_text_pm"] = output_info_text_pm
    return elements
