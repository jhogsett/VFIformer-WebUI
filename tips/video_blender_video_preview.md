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
    - There must be no other PNG files in the same directory
