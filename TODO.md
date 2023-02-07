### to do list

[ ] look into referencing VFIformer inside an intact subdirectory
[ ] see if a mention is needed of VFIformer license since I borrowed code
[ ] incorporate use of Real-ESRGAN tool for frame restoration/upscaling
[ ] clean up multiple util files in root directory
[ ] do I need the "fix gradio phoning home" fix like in automatic1111?
[ ] text file in the "run" directory with details like exact original filenames

Experiments

[ ] can some lost detail be recovered with multiple passes? Idea: use frames created adjacent to the outer frames + re-interpolation of some frames to try to bring that detail towards the center frames, where it's lost the most.

[ ] see if it's possible to zero-in on a specific between time, such as 0.333, by repeated targeted splitting
    341 / 2**10 = 0.3330
    683 / 2**10 = 0.6669

    method:
    - specify a target time 
    - based on the current splits, show the actual closest time it can reach
    - code will require a multiple of 1 / 2**splits
    - after a split, it will only recurse into the half that gets closer to target
    - at the end it won't be a continuous sequence, the last image will be the reached target
