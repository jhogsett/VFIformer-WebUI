import gradio as gr
from webui_utils.simple_utils import restored_frame_fractions, restored_frame_predictions
from webui_utils.icons import TOOLS_ICON, GEAR_ICON, INFO_ICON, UNDER_CONST, FILE_ICON, NUMBERS_ICON, ROCKET_ICON, PROPERTIES

def create_ui(config, video_blender_projects):
    gr.HTML("VFIformer Web UI", elem_id="appheading")

    with gr.Tab("Frame Interpolation"):
        gr.HTML("Divide the time between two frames to any depth, see an animation of result and download the new frames", elem_id="tabheading")
        with gr.Row():
            with gr.Column():
                img1_input_fi = gr.Image(type="filepath", label="Before Image", tool=None)
                img2_input_fi = gr.Image(type="filepath", label="After Image", tool=None)
                with gr.Row():
                    splits_input_fi = gr.Slider(value=1, minimum=1, maximum=config.interpolation_settings["max_splits"], step=1, label="Splits")
                    info_output_fi = gr.Textbox(value="1", label="Interpolated Frames", max_lines=1, interactive=False)
            with gr.Column():
                img_output_fi = gr.Image(type="filepath", label="Animated Preview", interactive=False)
                file_output_fi = gr.File(type="file", file_count="multiple", label="Download", visible=False)
        interpolate_button_fi = gr.Button("Interpolate", variant="primary")
        with gr.Accordion(INFO_ICON + " Tips", open=False):
            gr.Markdown("""
- Use _Frame Interpolation_ to
    - Reveal intricate motion between two frames of a video
    - Recreate a damaged frame
        - Set split count to _1_ and provide _adjacent frames_
        - _Frame Restoration_ can be used to recreate an arbitrary number of adjacent damaged frames""")

    with gr.Tab("Frame Search"):
        gr.HTML("Search for an arbitrarily precise timed frame and return the closest match", elem_id="tabheading")
        with gr.Row():
            with gr.Column():
                img1_input_fs = gr.Image(type="filepath", label="Before Image", tool=None)
                img2_input_fs = gr.Image(type="filepath", label="After Image", tool=None)
                with gr.Row():
                    splits_input_fs = gr.Slider(value=1, minimum=1, maximum=config.search_settings["max_splits"], step=1, label="Search Depth")
                    min_input_text_fs = gr.Text(placeholder="0.0-1.0", label="Lower Bound")
                    max_input_text_fs = gr.Text(placeholder="0.0-1.0", label="Upper Bound")
            with gr.Column():
                img_output_fs = gr.Image(type="filepath", label="Found Frame", interactive=False)
                file_output_fs = gr.File(type="file", file_count="multiple", label="Download", visible=False)
        search_button_fs = gr.Button("Search", variant="primary")
        with gr.Accordion(INFO_ICON + " Tips", open=False):
            gr.Markdown("""
- Use _Frame Search_ to synthesize a new frame at a precise time using _Targeted Interpolation_
    - Targeted Interpolation is a _Binary Search_:
        - The interval between two frames is _halved_ recursively toward the search window
        - A new _between frame_ is interpolated at each step
        - A matching frame is returned if found inside the search window, or when the search depth is reached
    - _Search Depth_ should be set high if a precisely timed frame is needed
    - A low value for _Search Depth_ is faster but may return an inaccurate or outside the search window result""")

    with gr.Tab("Video Inflation"):
        gr.HTML("Double the number of video frames to any depth for super slow motion", elem_id="tabheading")
        with gr.Row():
            with gr.Column():
                input_path_text_vi = gr.Text(max_lines=1, placeholder="Path on this server to the frame PNG files", label="Input Path")
                output_path_text_vi = gr.Text(max_lines=1, placeholder="Where to place the generated frames, leave blank to use default", label="Output Path")
                with gr.Row():
                    splits_input_vi = gr.Slider(value=1, minimum=1, maximum=10, step=1, label="Splits")
                    info_output_vi = gr.Textbox(value="1", label="Interpolations per Frame", max_lines=1, interactive=False)
        gr.Markdown("*Progress can be tracked in the console*")
        interpolate_button_vi = gr.Button("Interpolate Series (this will take time)", variant="primary")
        with gr.Accordion(INFO_ICON + " Tips", open=False):
            gr.Markdown("""
- _Video Inflation_ uses _Frame Interpolation_ to double a video's frame count any number of times
- This has many useful purposes:
    - Create a Super-Slow-Motion video
    - Recover the original real-time video from a time lapse video or GIF
    - Turn discrete motion continuous, like a second hand of a ticking clock
    - Frame Rate conversion

# Important
- This process will be slow, perhaps many hours long!
- Progress will be shown in the console using a standard _tqdm_ progress bar
- The browser window can be safely closed without interupting the process
- Currently there isn't an automatic way to resume a stalled inflation
    - Suggestion:
        - Set aside the rendered frames from the _input path_
        - Re-run the inflation
        - Use the _Resequence Files_ tool to rename the the two sets of rendered frames so they can be recombined""")

    with gr.Tab("Resynthesize Video"):
        gr.HTML("Interpolate replacement frames from an entire video for use in movie restoration", elem_id="tabheading")
        with gr.Row():
            with gr.Column():
                input_path_text_rv = gr.Text(max_lines=1, placeholder="Path on this server to the frame PNG files", label="Input Path")
                output_path_text_rv = gr.Text(max_lines=1, placeholder="Where to place the generated frames, leave blank to use default", label="Output Path")
        gr.Markdown("*Progress can be tracked in the console*")
        resynthesize_button_rv = gr.Button("Resynthesize Video (this will take time)", variant="primary")
        with gr.Accordion(INFO_ICON + " Tips", open=False):
            gr.Markdown("""
- _Resynthesize Video_ creates a set of replacement frames for a video by interpolating new ones between all existing frames
    - The replacement frames can be be used with _Video Blender_ to replace a video's damaged frames with clean substitutes
- How it works
    - For each new frame, the two adjacent original frames are used to interpolate a new _replacement frame_ using VFIformer
    - Example:
        - create a new frame #1 by interpolating a _between frame_ using original frames #0 and #2
        - then create a new frame #2 using original frames #1 and #3
        - and so on for all frames in the original video
    - When done, there will be a complete set of synthesized replacement frames, matching the ones from the original video
        - The _first_ and _last_ original frames cannot be resynthesized
        - When using _Video Blender_ ensure frame #0 from the original video PNG filesis is not present
- How to use the replacement frames
    - _Video Blender_ can be used to manually step through a video and replace frames one at a time from a restoration set
- Why this works
    - A video may have a single damaged frame between two clean ones
    - Examples: a bad splice, a video glitch, a double-exposed frame due to frame rate mismatch, etc.
    - VFIformer excels at detecting motion in all parts of a scene, and will very accurately create a new clean replacement frame
- Sometimes it doesn't work
    - Replacement frames cannot be resynthesized when there are not two CLEAN adjacent original frames
        - _Frame Restoration_ can be used to recover an arbitrary number of adjacent damaged frames
    - Transitions between scenes will not produce usable resynthesized frames""")

    with gr.Tab("Frame Restoration"):
        gr.HTML("Restore multiple adjacent bad frames using precision interpolation", elem_id="tabheading")
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    img1_input_fr = gr.Image(type="filepath", label="Frame Before Replacement Frames", tool=None)
                    img2_input_fr = gr.Image(type="filepath", label="Frame After Replacement Frames", tool=None)
                with gr.Row():
                    frames_input_fr = gr.Slider(value=config.restoration_settings["default_frames"], minimum=1, maximum=config.restoration_settings["max_frames"], step=1, label="Frames to Restore")
                    precision_input_fr = gr.Slider(value=config.restoration_settings["default_precision"], minimum=1, maximum=config.restoration_settings["max_precision"], step=1, label="Search Precision")
                with gr.Row():
                    times_default = restored_frame_fractions(config.restoration_settings["default_frames"])
                    times_output_fr = gr.Textbox(value=times_default, label="Frame Search Times", max_lines=1, interactive=False)
            with gr.Column():
                img_output_fr = gr.Image(type="filepath", label="Animated Preview", interactive=False)
                file_output_fr = gr.File(type="file", file_count="multiple", label="Download", visible=False)
        predictions_default = restored_frame_predictions(config.restoration_settings["default_frames"], config.restoration_settings["default_precision"])
        predictions_output_fr = gr.Textbox(value=predictions_default, label="Predicted Matches", max_lines=1, interactive=False)
        restore_button_fr = gr.Button("Restore Frames", variant="primary")
        with gr.Accordion(INFO_ICON + " Tips", open=False):
            gr.Markdown("""
- _Frame Restoration_ uses _Frame Search_ to create restored frames for a set of adjacent damaged ones
- The count of damaged frames and a pair of outer _clean_ frames are provided
- _Targeted interpolation_ is used to resynthesize a set of replacement frames at precise times

# Important
- Provide only CLEAN frames adjacent to the damaged ones
    - The frames should not cross scenes
    - Motion that is too fast may not produce good results
- Set _Frames to Restore_ to the exact number of needed replacement frames for accurate results
- _Frame Search Times_ shows the fractional search times for the restored frames
    - Example with 4 frames:
    - If there are 2 good frames _A_ and _D_ and 2 bad frames _b_ and _c_:
        - A---b---c---D
        - Replacement frame B is 1/3 of the way between frames A and D
        - Replacement frame C is 2/3 of the way between frames A and D
        - _Targeted Interpolation_ creates synthesized frames at these precise times
- Set _Search Precision_ to the _search depth_ needed for accuracy
    - Low _Search Precision_ is faster but can lead to repeated or poorly-timed frames
    - High _Search Precision_ takes longer but can produce near-perfect results
- _Predicted Matches_ estimates the frame times based on _Frames to Restore_ and _Search Precision_
    - Actual found frames may differ from predictions
    - A warning is displayed if _Search Precision_ should be increased due to repeated frames""")

    with gr.Tab("Video Blender"):
        gr.HTML("Combine original and replacement frames to manually restore a video", elem_id="tabheading")
        tabs_video_blender = gr.Tabs()
        with tabs_video_blender:
            with gr.Tab("Project Settings", id=0):
                with gr.Row():
                    input_project_name_vb = gr.Textbox(label="Project Name")
                    projects_dropdown_vb = gr.Dropdown(label=PROPERTIES + " Saved Projects", choices=video_blender_projects.get_project_names())
                    load_project_button_vb = gr.Button(PROPERTIES + " Load").style(full_width=False)
                    save_project_button_vb = gr.Button(PROPERTIES + " Save").style(full_width=False)
                with gr.Row():
                    input_project_path_vb = gr.Textbox(label="Project Frames Path", placeholder="Path to frame PNG files for video being restored")
                with gr.Row():
                    input_path1_vb = gr.Textbox(label="Original / Video #1 Frames Path", placeholder="Path to original or video #1 PNG files")
                with gr.Row():
                    input_path2_vb = gr.Textbox(label="Alternate / Video #2 Frames Path", placeholder="Path to alternate or video #2 PNG files")
                load_button_vb = gr.Button("Open Video Blender Project " + ROCKET_ICON, variant="primary")
                with gr.Accordion(INFO_ICON + " Tips", open=False):
                    gr.Markdown("""
- Set up the project with three directories, all with PNG files (only) with the _same file count, dimensions and starting sequence number_
- The _Original / Video #1 Frames Path_ should have the _original PNG files_ from the video being restored
- The _Project Frames Path_ should start with a _copy of the original PNG files_ as a baseline set of frames
- The _Alternate / Video #2 Frames Path_ directory should have a set of _replacement PNG files_ used for restoration
    - Replacement frames can be created using the _Resynthesize Video_ tool

# Important
- All paths must have _corresponding filenames, sequence numbers and PNG dimensions_
    - _Resequence Files_ can be used to rename a set of PNG files
    - If _Resynthesize Video_ was used to create a set of restoration frames, there will not be a frame #0 nor a final frame
        - Be sure frame #0 is NOT present in the _Original_ and _Alternate_ PNG file sets to avoid a off-by-one error
- For _Video Preview_ to work properly:
    - The files in each directory must have the _same base filename and numbering sequence_
    - `ffmpeg.exe` must be available on the _system path_

# Project Management
- To save a settings for a project:
    - After filling out all project text boxes, click _Save_
    - A new row will be added to the projects file `./video_blender_projects.csv`
    - To see the new project in the dropdown list:
    - Restart the application via the Tools page, or from the console
- To load settings for a project
    - Choose a project by name from the_Saved Project Settings_ DropDown
    - Click _Load_
    - Then cick _Open Video Blender Project_ to load the project and go to the _Frame Chooser_

General Use
- This tool can also be used any time there's a need to mix three videos, selectively replacing frames in one with frames from two others
- The Video Preview tab can be used to create and watch a preview video for any set of PNG files""")

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
                        preview_video_vb = gr.Button("Preview Video")
                    with gr.Column():
                        output_img_path2_vb = gr.Image(label="Repair / Path 2 Frame", interactive=False, type="filepath")
                    with gr.Column():
                        use_path_1_button_vb = gr.Button("Use Path 1 Frame | Next >", variant="primary", elem_id="actionbutton")
                        use_path_2_button_vb = gr.Button("Use Path 2 Frame | Next >", variant="primary", elem_id="actionbutton")
                        with gr.Row():
                            prev_frame_button_vb = gr.Button("< Prev Frame", variant="primary")
                            next_frame_button_vb = gr.Button("Next Frame >", variant="primary")
                        fix_frames_button_vb = gr.Button("Fix Frames")

                with gr.Accordion(INFO_ICON + " Tips", open=False):
                    gr.Markdown("""
# Important
The green buttons copy files!
- Clicking copies a frame PNG file from the corresponding directory to the project path
- Undo simply by going back and choosing the other path
- The remaining buttons do not alter the project

Use the Next Frame > and < Prev Frame buttons to step through video one frame at a time
- Tip: After clicking a button, SPACEBAR can be used to click repeatedly

Clicking _Preview Video_ will take you to the _Preview Video_ tab
- The current set of project PNG frame files can be quickly rendered into a preview video and watched

Clicking _Fix Frames_ will take you to the _Frame Fixer_ tab
- Make quick replacements for a series of damaged frames
- See an animated preview of the recreated frames
- Overwrite the damaged frames if good enough
""")

            with gr.Tab("Frame Fixer", id=2):
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            project_path_ff = gr.Text(label="Video Blender Project Path", placeholder="Path to video frame PNG files")
                        with gr.Row():
                            input_clean_before_ff = gr.Number(label="Last clean frame BEFORE damaged ones", value=0, precision=0)
                            input_clean_after_ff = gr.Number(label="First clean frame AFTER damaged ones", value=0, precision=0)
                        with gr.Row():
                            preview_button_ff = gr.Button(value="Preview Fixed Frames", variant="primary")
                    with gr.Column():
                        preview_image_ff = gr.Image(type="filepath", label="Fixed Frames Preview", interactive=False)
                        fixed_path_ff = gr.Text(label="Path to Restored Frames", interactive=False)
                        use_fixed_button_ff = gr.Button(value="Apply Fixed Frames", elem_id="actionbutton")
                with gr.Accordion(INFO_ICON + " Tips", open=False):
                    gr.Markdown("""
- When arrving at this tab via the _Frame Chooser_ Fix Frames button, the following fields are pre-filled from the project:
    - Video Blender Project Path (PNG files for video being blended)
    - Last clean frame BEFORE damaged ones (current frame from _Frame Chooser_)

# Important

- _Last clean frame BEFORE damaged ones_ MUST be the last clean frame before the set of damaged ones
- _First clean frame AFTER damaged ones_ MUST be the first clean frame after the set of damaged ones
- Frames may not be fixable if there's a scene change, motion is too fast, or the clean frames are too far apart""")

            with gr.Tab("Video Preview", id=3):
                with gr.Row():
                    video_preview_vb = gr.Video(label="Preview", interactive=False, include_audio=False) #.style(width=config.blender_settings["preview_width"]) #height=config.blender_settings["preview_height"],
                preview_path_vb = gr.Textbox(max_lines=1, label="Path to PNG Sequence", placeholder="Path on this server to the PNG files to be converted")
                with gr.Row():
                    render_video_vb = gr.Button("Render Video", variant="primary")
                    input_frame_rate_vb = gr.Slider(minimum=1, maximum=60, value=config.png_to_mp4_settings["frame_rate"], step=1, label="Frame Rate")
                with gr.Accordion(INFO_ICON + " Tips", open=False):
                    gr.Markdown("""
- When arrving at this tab via the _Frame Chooser_ Preview Video button, the _Path to PNG Sequence_ is automatically filled with the Video Blender project path
    - Simply click _Render Video_ to create and watch a preview of the project in its current state
- Preview videos are rendered in the directory set by the `directories:working` variable in `config.yaml`
    - The directory is `./temp` by default and is NOT automatically purged

# Tip
- This tab can be used to render and watch a preview video for any directory of video frame PNG files
- Requirements:
    - The files must be video frame PNG files with the same dimensions
    - The filenames must all confirm to the same requirements:
    - Have the same starting base filename
    - Followed by a frame index integer, all zero-filled to the same width
    - Example: `FRAME001.png` through `FRAME420.png`
    - There must be no other PNG files in the same directory""")

    with gr.Tab("Tools" + TOOLS_ICON):
        with gr.Tab("File Conversion " + FILE_ICON):
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
                with gr.Accordion(INFO_ICON + " Tips", open=False):
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
                with gr.Accordion(INFO_ICON + " Tips", open=False):
                    gr.Markdown("""
- The filename pattern should be based on the number of PNG files to ensure they're read in alphanumeric order
- Example: For a PNG sequence with _24,578_ files and filenames like "TENNIS24577.png", the pattern should be "TENNIS%05d.png"
- The special pattern "auto" can be used to detect the pattern automatically. This works when:
    - The only PNG files present are the frame images
    - All files have the same naming pattern, starting with a base filename, and the same width zero-filled frame number
    - The first found PNG file follows the same naming pattern as all the other files
- The _Video Preview_ tab on the _Video Blender_ page can be used to watch a preview video of a set of PNG files""")

            with gr.Tab("GIF to PNG Sequence " + UNDER_CONST):
                gr.Markdown("Planned: Convert a GIF to a PNG sequence")

            with gr.Tab("PNG Sequence to GIF " + UNDER_CONST):
                gr.Markdown("Planned: Convert a PNG sequence to a GIF, specify duration and looping")

        with gr.Tab("Resequence Files " + NUMBERS_ICON):
            gr.HTML("Rename a PNG sequence for import into video editing software", elem_id="tabheading")
            with gr.Row():
                with gr.Column():
                    input_path_text2 = gr.Text(max_lines=1, placeholder="Path on this server to the files to be resequenced", label="Input Path")
                    with gr.Row():
                        input_filetype_text = gr.Text(value="png", max_lines=1, placeholder="File type such as png", label="File Type")
                        input_newname_text = gr.Text(value="pngsequence", max_lines=1, placeholder="Base filename for the resequenced files", label="Base Filename")
                    with gr.Row():
                        input_start_text = gr.Text(value="0", max_lines=1, placeholder="Starting integer for the sequence", label="Starting Sequence Number")
                        input_step_text = gr.Text(value="1", max_lines=1, placeholder="Integer tep for the sequentially numbered files", label="Integer Step")
                        input_zerofill_text = gr.Text(value="-1", max_lines=1, placeholder="Padding with for sequential numbers, -1=auto", label="Number Padding")
                    with gr.Row():
                        input_rename_check = gr.Checkbox(value=False, label="Rename instead of duplicate files")
                    resequence_button = gr.Button("Resequence Files", variant="primary")
            with gr.Accordion(INFO_ICON + " Tips", open=False):
                gr.Markdown("""
_Resequence Files_ can be used to make a set of PNG files ready for important into video editing software

# Important
The only PNG files present in the _Input Path_ should be the video frame files

- _File Type_ is used for a wildcard search of files
- _Base Filename_ is used to name the resequenced files with an added frame number
- _Starting Sequence Number_ should usually be _0_
    - A different value might be useful if inserting a PNG sequence into another
- _Integer Step_ should usually be _1_
    - This sets the increment between the added frame numbers
- _Number Padding_ should usually be _-1_ for automatic detection
    - Set to another value if a specific width of digits is needed for frame numbers
- Leave _Rename instead of duplicate files_ unchecked if the original files may be needed
    - They be useful for tracking back to a source frame""")

        with gr.Tab("GIF to Video " + UNDER_CONST):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("""
Idea: Recover the original video from animated GIF file
- split GIF into a series of PNG frames
- use R-ESRGAN 4x+ to restore and/or upscale
- use VFIformer to adjust frame rate to real time
- reassemble new PNG frames into MP4 file""")

        with gr.Tab("Upscaling " + UNDER_CONST):
            gr.Markdown("Future: Use Real-ESRGAN 4x+ to restore and/or upscale images")

        with gr.Tab("Options" + GEAR_ICON):
            restart_button = gr.Button("Restart App", variant="primary").style(full_width=False)

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
    elements["fix_frames_button_vb"] = fix_frames_button_vb
    elements["preview_video_vb"] = preview_video_vb
    elements["project_path_ff"] = project_path_ff
    elements["input_clean_before_ff"] = input_clean_before_ff
    elements["input_clean_after_ff"] = input_clean_after_ff
    elements["preview_button_ff"] = preview_button_ff
    elements["preview_image_ff"] = preview_image_ff
    elements["fixed_path_ff"] = fixed_path_ff
    elements["use_fixed_button_ff"] = use_fixed_button_ff
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

# this created a code box in markdown for some reason
# # Important
#     - _Last clean frame BEFORE damaged ones_ MUST be the last clean frame before the set of damaged ones
#     - _First clean frame AFTER damaged ones_ MUST be the first clean frame after the set of damaged ones
#     - Frames may not be fixable in this cases:
#         - If a scene change occurs
#         - If the motion is too fast
#         - If the before and after clean frames are too far apart
