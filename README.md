# VFIformer-WebUI
## A Gradio-based Web UI for using VFIformer

![image](https://user-images.githubusercontent.com/825994/216856563-6027bddf-c617-420a-8652-5228bfacb3b5.png)

![interpolated_frames0](https://user-images.githubusercontent.com/825994/217050627-e0fd6e17-1c53-49aa-88d6-72a9717b2c13.gif)

I have been writing my own Python code for some time to use the [VFIformer](https://github.com/dvlab-research/VFIformer) video frame interpolation engine for various purposes (here's an [example video](https://www.youtube.com/watch?v=JhibFQvP7X0) from my [YouTube channel](https://www.youtube.com/@jerryhogsett)). I thought, why don't I start learning Gradio by building a WebUI for this tool that I love and use so much. Of course, and make it avaiable to the public. 

_My code builds on their repo and borrows some code, but makes no changes._

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
- It shouldn't introduce any additional requirements over what VFIformer needs
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

- Click the upper left panel or drag and drop a "before" frame
- Do the same for the lower left panel, for an "after" frame
  - sample images can be found in the `images` directory
- Choose the number of splits
  - The number of created "between" frames will be (2 ** splits - 1)
  - A large split count will take a long time to complete (9 splits took > 16 minutes on my system)
- Click Interpolate
  - When the split count is > 1, a progress bar is shown in the console window
- When the process completes, an animated GIF shows the result of the interpolation
- The original and generated PNG frames are saved in a sequentially numbered `run` directory within `output\interpolate`
- The animated GIF preview is also saved

# Command Line Tools

The core components also allow command line use.

## interpolate.py

Create an interpolated frame between two frames

Example: `python interpolate.py`
- loads `images/image0.png` and `images/image2.png`
- interpolates and saves `images/image1.png`
- use `python interpoloate.py --help` for arguments

## deep_interpolate.py

Create a chosen number of interplolated frames between two frames

Example: `python deep_interpolate.py --depth 2`
- loads images/image0.png and images/image2.png
- interpolates three evenly-speced between frames
- the original and new frames are put in `output/interpolated_frame0.png` ... `interpolated_frame4.png`
- the `depth` argument specifies the number of *doublings* of the effective frame rate
  - the number of newly created frames = 2 ** depth - 1

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
- interpolate_settings\[gif_duration\]
  - total time in ms for the animated GIF preview
  - default is 3000
  
### Thanks!

Thanks! to the VFIformer folks for their amazing tool 
- https://github.com/dvlab-research/VFIformer

Thanks! to the stable-diffusion-webui folks for their great UI, amazing tool, and for inspiring me to learn Gradio
- https://github.com/AUTOMATIC1111/stable-diffusion-webui

Thanks to Gradio for their easy-to-use Web UI building tool and great docs
- https://gradio.app/
- https://github.com/gradio-app/gradio

### My Public Uses of VFIformer

YouTube
- Feb 01 2023 "Fun with AI: De-Ticking a Ticking Clock" https://youtu.be/JhibFQvP7X0
- Jan 28 2023 "Fun with AI: Infinite Slow Motion" https://youtu.be/sKQKuYU-fcQ
- Jan 24 2023 "Fun with AI: Me as a Baby, Restoring 60 year old 8mm film" https://youtu.be/sKQKuYU-fcQ
