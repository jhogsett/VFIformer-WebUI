import os
import glob
from ffmpy import FFmpeg, FFprobe
from .image_utils import gif_frame_count
from .file_utils import split_filepath

# ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames -print_format default=nokey=1:noprint_wrappers=1 Big_Buck_Bunny_1080_10s_20MB.mp4
def MP4_frame_count(input_path : str) -> int:
    ff = FFprobe(inputs= {input_path : "-count_frames -show_entries stream=nb_read_frames -print_format default=nokey=1:noprint_wrappers=1"})
    return ff.run()

QUALITY_NEAR_LOSSLESS = 17
QUALITY_SMALLER_SIZE = 28
QUALITY_DEFAULT = 23

def determine_pattern(input_path : str):
    files = sorted(glob.glob(os.path.join(input_path, "*.png")))
    first_file = files[0]
    file_count = len(files)
    num_width = len(str(file_count))
    name_part, ext_part = os.path.splitext(first_file)
    return f"{name_part[:-num_width]}%0{num_width}d{ext_part}"

# ffmpeg -i BALLOON%03d.png -c:v libx264 -r 30 -pix_fmt yuv420p frames.mp4
# if filename_pattern is "auto" it uses the filename of the first found file
# and the count of file to determine the pattern, .png as the file type
def PNGtoMP4(input_path : str, filename_pattern : str, frame_rate : int, output_filepath : str, crf : int = 23):
    if filename_pattern == "auto":
        filename_pattern = determine_pattern(input_path)
    ff = FFmpeg(inputs= {os.path.join(input_path, filename_pattern) : None},
                outputs={output_filepath : f"-c:v libx264 -r {frame_rate} -pix_fmt yuv420p -crf {crf}"},
                global_options="-y")
    cmd = ff.cmd
    ff.run()
    return cmd

# ffmpeg -y -i frames.mp4 -filter:v fps=25 -pix_fmt rgba -start_number 0 output_%09d.png
def MP4toPNG(input_path : str, filename_pattern : str, frame_rate : int, output_path : str, start_number : int = 0):
    ff = FFmpeg(inputs= {input_path : None},
                outputs={os.path.join(output_path, filename_pattern) : f"-filter:v fps={frame_rate} -pix_fmt rgba -start_number {start_number}"},
                global_options="-y")
    cmd = ff.cmd
    ff.run()
    return cmd

# making a high quality GIF from images requires first creating a color palette,
# then supplying it to the conversion command
# https://stackoverflow.com/questions/58832085/colors-messed-up-distorted-when-making-a-gif-from-png-files-using-ffmpeg

# ffmpeg -i gifframes_%02d.png -vf palettegen palette.png
def PNGtoPalette(input_path : str, filename_pattern : str, output_filepath : str):
    if filename_pattern == "auto":
        filename_pattern = determine_pattern(input_path)
    ff = FFmpeg(inputs= {os.path.join(input_path, filename_pattern) : None},
                outputs={output_filepath : "-vf palettegen"},
                global_options="-y")
    cmd = ff.cmd
    ff.run()
    return cmd

# ffmpeg -i gifframes_%02d.png -i palette.png -lavfi paletteuse video.gif
# if filename_pattern is "auto" it uses the filename of the first found file
# and the count of file to determine the pattern, .png as the file type
def PNGtoGIF(input_path : str, filename_pattern : str, output_filepath : str):
    if filename_pattern == "auto":
        filename_pattern = determine_pattern(input_path)
    output_path, base_filename, _ = split_filepath(output_filepath)
    palette_filepath = os.path.join(output_path, base_filename + "-palette.png")
    palette_cmd = PNGtoPalette(input_path, filename_pattern, palette_filepath)

    ff = FFmpeg(inputs= {
                    os.path.join(input_path, filename_pattern) : None,
                    palette_filepath : None},
                outputs={output_filepath : "-lavfi paletteuse"},
                global_options="-y")
    cmd = ff.cmd
    ff.run()
    return "\n".join([palette_cmd, cmd])

# ffmpeg -y -i images\example.gif -start_number 0 gifframes_%09d.png
def GIFtoPNG(input_path : str, output_path : str, start_number : int = 0):
    _, base_filename, _ = split_filepath(input_path)
    frame_count = gif_frame_count(input_path)
    num_width = len(str(frame_count))
    filename_pattern = f"{base_filename}%0{num_width}d.png"
    ff = FFmpeg(inputs= {input_path : None},
                outputs={os.path.join(output_path, filename_pattern) : f"-start_number {start_number}"},
                global_options="-y")
    cmd = ff.cmd
    ff.run()
    return cmd

