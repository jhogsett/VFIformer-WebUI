**Upscale Frames** - Use _Real-ESRGAN_ to Enlarge and Clean Frames

## Uses
- Increase the size of video frames
- Clean up dirty/deteriorated frames
- Use without upscaling to clean frames

## Important
Real-ESRGAN must be installed locally to use
1. See the _Resources_ tab or go to [Real ESRGAN Github](https://github.com/xinntao/Real-ESRGAN) to access Real-ESRGAN repository
1. Clone their repo to its own directory and follow their instructions for local setup
1. Copy the `realesrgan` directory to your `VFIformer-WebUI` directory
* The _Real-ESRGAN 4x+_ model (65MB) will automatically download on first use

## How It Works
1. Set _Input Path_ to a directory on this server to the PNG files to be upscaled
1. Set _Output Path_ to a directory on this server for the upscaled PNG files
    - Output Path can be left blank to use the default folder
    - The default folder is set by the `config.directories.output_upscaling` setting
1. Set _Frame Upscale Factor_ for the desired amount of frame enlargement
    - The factor can be set between 1.0 and 8.0 in 0.05 steps
    - Real-ESRGAN does upscaling if the factor if > 1.0
        - It also removes dirt and noise even if not upscaling
1. Click _Upscale Frames_
1. _Real-ESRGAN_ is used on each frame in the input path
    - Frames are cleaned up, and enlarged if necessary
    - The new frames are copied to the output path
1. When complete, the output path will contain a new set of frames
