# VFIformer-WebUI - AI-Based Movie Restoration

![Screenshot_20230217_031421-900w](https://user-images.githubusercontent.com/825994/219824616-7340049a-3bbd-44b1-a2c5-a80b6d2a8195.PNG)

| ![example](https://user-images.githubusercontent.com/825994/217553208-8b482d9a-4567-4af4-918d-a5938f709215.gif) | 
|:--:| 
| Example - Interpolated Frames |

| [Demo of 32X Video Inflation with marked original frames](https://youtu.be/rOiALIN805w) | 
|:--:| 
| Example - Video Inflation (YouTube) |

# VFIformer-WebUI Features

### Gradio-App based Web UI for using _VFIformer_ 
- Perform state of the art AI Video Frame Interpolation
- A Suite of movie restoration tools built around VFIformer

### Frame Interpolation
- Reveal hidden motion between two video frames
- Restore a missing or damaged frame

### Frame Search
- Binary Search Interpolation
- Synthesize a _between_ frame at a precise time

### Video Inflation
- Double a movie's frame count any number of times for super-slow-motion

### Resynthesize Video
- Automatically create a set of synthesized frames for use in restoring films

### Frame Restoration
- Like magic, restore an arbitrary number of adjacent damaged frames

### Video Blender
- Easy tool to step through a movie replacing damaged frames
- With in-place frame repair and video preview

### File Conversion
- Convert MP4 to PNG Sequence, PNG Sequence to MP4, GIF to PNG Sequence, PNG Sequence to GIF

### Resequence Files
- Automatically re-number a set of PNG files for import into video editing software

### FPS Conversion
- Convert a video from any FPS to any other FPS using Frame Search

# Set Up For Use

1. Get VFIformer working on your local system
- See their repo at [https://github.com/dvlab-research/VFIformer](https://github.com/dvlab-research/VFIformer)
- I run locally with:
  - Anaconda 23.1.0
  - Python 3.10.9
  - Torch 1.13.1
  - Cuda 11.7
  - NVIDIA RTX 3090
  - Windows 11
2. Clone this repo in a separate directory and copy all directories/files on top of your *working* VFIformer installation
- This code makes no changes to their original code (but borrows some) and causes no conflicts with it
- It shouldn't introduce any additional requirements over what VFIformer and Gradio-App needs
3. If it's set up properly, the following command should write a new file `images/image1.png` using default settings

`python interpolate.py`

# Alternate Set Up / Development

1. Get VFIformer working on your local system
- See their repo at [https://github.com/dvlab-research/VFIformer](https://github.com/dvlab-research/VFIformer)
- I run locally with:
  - Anaconda 23.1.0
  - Python 3.10.9
  - Torch 1.13.1
  - Cuda 11.7
  - NVIDIA RTX 3090
  - Windows 11
2. Clone this repo to a directory in which you intend to use the app and/or develop on it
3. Copy the following directories from your *working* VFIformer installation to this directory:
- `dataloader`
- `models`
- `pretrained_models`
- `utils`
4. If it's set up properly, the following command should write a new file `images/image1.png`

`python interpolate.py`

# Starting Web UI Application

The application can be started in any of these ways:
- `webui.bat`
- `python webui.py`

# Using Web UI

## Frame Interpolation

- Click the upper left panel or drag and drop a *before* frame
- Do the same for the lower left panel, for an *after* frame
  - sample images can be found in the `images` directory
- Choose the number of splits
  - The number of created "between" frames will be (2 ** splits - 1)
  - A large split count will take a long time to complete
  - 10 splits took > 8 minutes on my system with the example images
- Click Interpolate
  - When the split count is > 1, a progress bar is shown in the console window
- When the process completes, an animated GIF shows the result of the interpolation
- The original and generated PNG frames are saved in a sequentially numbered `run` directory within `output\interpolation`
- The animated GIF preview file and a ZIP of the frames are also saved
- The GIF, ZIP and a TXT file report are downloadable from the UI

## Frame Search

- Click the upper left panel or drag and drop a *before* frame
- Do the same for the lower left panel, for an *after* frame
  - sample images can be found in the `images` directory
- Choose the search depth
  -  tip: use a deep search depth for high precision
- Enter a minumum and maximum search range
- Click Search
- The closest matching frame will shown in the preview window
- The generated PNG is saved in a sequentially numbered `run` directory within `output\search`
- It is also made available for download from the UI
- *See command line examples below*

## Video Inflation

- Enter Input and Output directories
  - The Input directory should contain a sequence of video frame PNG files
  - The Output directory can be left blank to save in a sequentially numbered `run` directory within `output\inflation`
  - The files will be read and processed in alphanumeric order
    - The *Resequence Files* tool can be used to sequentially number a set of PNG files
- Choose the number of splits
- Click Interpolate Series
- This will take a long time!
- A standard TQDM progress bar is shown in the console to track progress

## Tools - Resequence Files

- Enter a path to the files to be resequenced
- Enter a file type
  - this is used to search for files in the input path
  - it's also used to generate the file type for the output filenames
- Enter a base filename for the resequenced files
- Enter a starting sequence number
  - 0 is a typical value
  - a different value might be useful if inserting frames into another sequence
- Enter an integer step
  - 1 is a typical value
  - a different value might be useful in special situations
  - I used this in a [video](https://www.youtube.com/watch?v=rOiALIN805w) to overlay a set of watermarked *real* frames on top of an inflated set of video frames, where I needed each frame to be the next 32nd frame in the overall sequence
- Enter a number padding
  - -1 (automatic) is a typical value
  - this determines the zero-fill of the sequential number, and is used to ensure the frames are alphanumeric-sortable
  - *automatic* will determine this based on the number of files
  - a different value might be useful if inserting frames into another sequence
- Choose whether to rename (checked) or duplicate (unchecked) the files to resequence them
  - it can be handy to have the original set of frames, marked with their original frame ID, for troubleshooting
- Click Resequence Files
- A standard TQDM progress bar is shown in the console to track progress

# Command Line Tools

The core feature have command-line equivalents

[Wiki - Command Line Tools](https://github.com/jhogsett/VFIformer-WebUI/wiki/Command-Line-Tools)

# App Configuration

App configuration is set via `config.yaml`

### Notable settings
- model (parameter passed to VFIformer)
  - path to the VFIformer downloaded model
- gpu_ids (parameter passed to VFIformer)
  - should be "0" to use the local GPU and "-1" for CPU
  - I tried and was unable to run VFIformer without the GPU
- auto_launch_browser
  - True to open the app in a browser tab
- server_port
  - local port to use for Web UI access
  - default is `7862` rather than the usual Gradio default of `7860` to avoid conflicting with other Gradio apps
- server_name
  - server address to use for Gradio http server
  - default is "0.0.0.0" which makes the app available on the local network as well
  - to prevent this, set to "127.0.0.1" or None
- interpolation_settings\[gif_duration\]
  - total time in ms for the animated GIF preview
  - default is 3000

# Future Plans
- incorporate Real-ESRGAN for frame restoration and upscaling
  - https://github.com/xinntao/Real-ESRGAN
- add a GIF-to-MP4 feature to recover the original video from an animated GIF
  - uses Real-ESRGAN to denoise the GIF frames and upscale them
  - uses VFIformer to fill in missing frames
  - saved as a MP4 files or PNG sequence
- add tools to easily switch between GIF PNG & MP4 formats
- make the tool available in a Hugging Face space https://huggingface.co/
  - I could use help with this
- Suggestions are very welcome
- Contributions are also very welcome

# Thanks!

Thanks! to the VFIformer folks for their amazing tool
- https://github.com/dvlab-research/VFIformer

Thanks! to the stable-diffusion-webui folks for their great UI, amazing tool, and for inspiring me to learn Gradio
- https://github.com/AUTOMATIC1111/stable-diffusion-webui

Thanks to Gradio for their easy-to-use Web UI building tool and great docs
- https://gradio.app/
- https://github.com/gradio-app/gradio

# Credits

Royalty-Free Videos used for the examples
- "FunfaIr in Barcelona" https://motionarray.com/stock-video/funfair-in-barcelona-1163645/
- "Batter Misses A Pitch" https://motionarray.com/stock-video/batter-misses-a-pitch-1231021/
- "Bursting A Balloon" https://motionarray.com/stock-video/bursting-a-balloon-253645/

# My Public Uses of VFIformer

YouTube
- Feb 01 2023 "Fun with AI: De-Ticking a Ticking Clock" https://youtu.be/JhibFQvP7X0
- Jan 28 2023 "Fun with AI: Infinite Slow Motion" https://youtu.be/sKQKuYU-fcQ
- Jan 24 2023 "Fun with AI: Me as a Baby, Restoring 60 year old 8mm film" https://youtu.be/PiLv5u1PYiE
