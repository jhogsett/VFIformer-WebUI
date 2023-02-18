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
- The Video Preview tab can be used to create and watch a preview video for any set of PNG files
