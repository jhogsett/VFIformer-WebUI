# VFIformer-WebUI
A Gradio-based Web UI for using VFIformer

![image](https://user-images.githubusercontent.com/825994/216856563-6027bddf-c617-420a-8652-5228bfacb3b5.png)

I have been writing my own Python code for some time to use the [VFIformer](https://github.com/dvlab-research/VFIformer) video frame interpolation engine for various purposes (here's an [example video](https://www.youtube.com/watch?v=JhibFQvP7X0) from my [YouTube channel](https://www.youtube.com/@jerryhogsett)).

I thought, why don't I start learning Gradio by building a WebUI for this tool that I love and use so much. Of course, and make it avaiable to the public.

My code builds on their repo and borrows some code, but makes no changes.

First I recommend cloning their repo at [https://github.com/dvlab-research/VFIformer](https://github.com/dvlab-research/VFIformer) locally and following those instructions to get it set up and running. You'll need to download the model, and you'll need a couple of video frames to test with. Their file demo.py can be used to create a between frame.

Once you have VFIformer up and running, place all files and directories from this repo on top of their cloned repo. I don't believe my code has any requirements above what theirs does.

To start the Web UI run "python webui.py". It should start up and open a tab in your browser. App settings are in the "config.yaml" file.

To use it:
- Click the upper left panel or drag and drop a "before" frame
- Do the same for the lower left panel, for an "after" frame
- Choose the number of splits
  - The number of created "between" frames will be (2 ** splits - 1)
  - A large split count will take a long time to complete
- Click Interpolate
- When the process completes, an animated GIF shows the result of the interpolation
- The original and generated PNG frames are saved in a sequentially numbered "run" folder (see config.yaml)
- The animated GIF is also saved

Note, when the split count is one, a download option is presented after generation
- This is to avoid a cumbersome interface downloading more than a single file
- A planned feature will allow downloading the set of frames in various formats (.zip, .gif, .mp4)
