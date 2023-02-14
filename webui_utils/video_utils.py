import os
from ffmpy import FFmpeg

# ffmpeg -i BALLOON%03d.png -c:v libx264 -r 30 -pix_fmt yuv420p frames.mp4
def PNGtoMP4(input_path : str, filename_pattern : str, frame_rate : int, output_filepath : str, crf : int = 23):
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
