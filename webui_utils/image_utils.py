"""Functions for dealing with images"""
from PIL import Image

def create_gif(images : dict, filepath : str, duration : int = 1000):
    """Create an animated GIF"""
    if len(images) > 1:
        images = [Image.open(image) for image in images]
        if len(images) == 1:
            images[0].save(filepath)
        else:
            images[0].save(filepath, save_all=True, append_images=images[1:],
                optimize=False, duration=duration, loop=0)

def gif_frame_count(filepath : str):
    """Get the number of frames of a GIF file"""
    gif = Image.open(filepath)
    if gif:
        return gif.n_frames
