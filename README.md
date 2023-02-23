[![Pylint](https://github.com/jhogsett/VFIformer-WebUI/actions/workflows/pylint.yml/badge.svg)](https://github.com/jhogsett/VFIformer-WebUI/actions/workflows/pylint.yml)
![pybadge](https://img.shields.io/badge/Python-3.10.9-4380b0)
![ptbadge](https://img.shields.io/badge/Torch-1.13.1-ee4b28)
![nvbadge](https://img.shields.io/badge/Cuda-11.7-76b900)

# VFIformer-WebUI - AI-Based Movie Restoration

![Screenshot_20230217_031421-900w](https://user-images.githubusercontent.com/825994/219824616-7340049a-3bbd-44b1-a2c5-a80b6d2a8195.PNG)

| Example - Interpolated Frames |
|:--:|
| ![example](https://user-images.githubusercontent.com/825994/217553208-8b482d9a-4567-4af4-918d-a5938f709215.gif) |

| Example - Video Inflation (YouTube) |
|:--:|
| [Demo of 32X Video Inflation with marked original frames](https://youtu.be/rOiALIN805w) |

# VFIformer-WebUI Features

_**Frame Interpolation**_
* Restore Missing Frames, Reveal Hidden Motion

_**Frame Search**_
* Synthesize Between Frames At Precise Times

_**Video Inflation**_
* Create Super Slow-Motion

_**Resynthesize Video**_
* Create a Complete Set of Replacement Frames

_**Frame Restoration**_
* Restore Adjacent Missing / Damaged

_**Video Blender**_
* Project-Based Movie Restoration

_**File Conversion**_
* Convert between PNG Sequences and Videos

_**Resequence Files**_
* Renumber for Import into Video Editing Software

_**Change FPS**_
* Convert any FPS to any other FPS

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
2. Clone this repo in a separate directory and copy all* directories/files on top of your *working* VFIformer installation
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

# Real-ESRGAN Add-On Set Up

1. Get _Real-ESRGAN_ working on your local system
- See their repo at [https://github.com/xinntao/Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)
2. Clone their repo to its own directory and follow their instructions for local setup
3. Copy the `realesrgan` directory to your `VFIformer-WebUI` directory
* The _Real-ESRGAN 4x+_ model (65MB) will automatically download on first use

# Starting Web UI Application

The application can be started in any of these ways:
- `webui.bat`
- `python webui.py`
  - _Command line arguments_
    - `--config_path path` path to alternate configuration file, default `config.yaml`
    - `--verbose` enables verbose output to the console, default False

# Using Web UI

## Frame Interpolation

1. Drag and drop, or click to upload _Before Frame_ and _After Frame_ PNG files
1. Set _Split Count_ to choose the number of new _Between Frames_
    - Each _split_ doubles the frame count
1. Click _Interpolate_
1. The _Animated Preview_ panel will show a GIF of the original and newly created frames
1. The _Download_ box gives access to
    - Animated GIF
    - ZIP of original and interpolated frames
    - TXT report

## Frame Search

1. Drag and drop, or click to upload _Before Frame_ and _After Frame_ PNG files
1. Choose a _Lower Bound_ and _Upper Bound_ for the search
    - The values must be between 0.0 and 1.0
1. Set _Search Precision_ per the desired timing accuracy
    - Low is faster but can lead to a poorly-timed frame
    - High produces near-perfect results but takes longer
1. Click _Search_
1. The _Found Frame_ panel will show the new frame
1. The _Download_ box gives access to
    - The found frame PNG file

## Video Inflation

1. Set _Input Path_ to a directory on this server to the PNG files to be inflated
1. Set _Output Path_ to a directory on this server for the inflated PNG files
    - Output Path can be left blank to use the default folder
    - The default folder is set by the `config.directories.output_inflation` setting
1. Set _Split Count_ for the number of new _between_ frames
    - The count of interpolated frames is computed by this formula:
        - F=2**S-1, where
        - F is the count of interpolated frames
        - S is the split count
1. Click _Inflate Video_
1. _Frame Interpolation_ is done between each pair of frames
    - New frames are created according to the split count
    - The original and new frames are copied to the output path
1. When complete, the output path will contain a new set of frames

## All Features

[Wiki - Home](https://github.com/jhogsett/VFIformer-WebUI/wiki)

# Command Line Tools

The core feature have command-line equivalents

[Wiki - Command Line Tools](https://github.com/jhogsett/VFIformer-WebUI/wiki/Command-Line-Tools)

# App Configuration

[Wiki - App Configuration](https://github.com/jhogsett/VFIformer-WebUI/wiki/App-Configuration)

# Future Ideas

- add Audio tools

# My Public Uses of VFIformer

YouTube
- Feb 01 2023 "Fun with AI: De-Ticking a Ticking Clock" https://youtu.be/JhibFQvP7X0
- Jan 28 2023 "Fun with AI: Infinite Slow Motion" https://youtu.be/sKQKuYU-fcQ
- Jan 24 2023 "Fun with AI: Me as a Baby, Restoring 60 year old 8mm film" https://youtu.be/PiLv5u1PYiE

# Acknowledgements

Thanks! to the VFIformer folks for their amazing AI Tool
- https://github.com/dvlab-research/VFIformer

Thanks! to the stable-diffusion-webui folks for their great UI, amazing tool, and for inspiring me to learn Gradio
- https://github.com/AUTOMATIC1111/stable-diffusion-webui

Thanks to Gradio for their easy-to-use Web UI building tool and great docs
- https://gradio.app/
- https://github.com/gradio-app/gradio

Royalty-Free Videos used for the examples
- "FunfaIr in Barcelona" https://motionarray.com/stock-video/funfair-in-barcelona-1163645/
- "Batter Misses A Pitch" https://motionarray.com/stock-video/batter-misses-a-pitch-1231021/
- "Bursting A Balloon" https://motionarray.com/stock-video/bursting-a-balloon-253645/
