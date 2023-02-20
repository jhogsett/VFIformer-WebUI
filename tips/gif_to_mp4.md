## Idea

Recover the original video from an animated GIF
- Split the GIF into a series of PNG frames
- Use _R-ESRGAN 4x+_ to restore and/or upscale the frames
- Use VFIformer AI to adjust the frame rate to real time
- Reassemble new PNG frames into a MP4 file
