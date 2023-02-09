## TO DO

Needed
- some kind of in-progress indication on video inflation and prevention of clicking submit again
- do I need the "fix gradio phoning home" fix like in stable-diffusion-webui?
- wiki content (unclutter the readme file)

Nice to have
- can the core code provide a way to allow the Gradio UI to update while in progress? 
- look into referencing VFIformer inside an intact subdirectory
- can a control be updated outside of the Gradio event loop? (might work to tap into event loop)
- add an about tab or page, links to VFIformer, Real-ESRGAN, Gradio and my repo
- better restart that actually reloads the model and recreates the UI (current restart is just a proof of concept)
- full auto-installation including VFIformer and Real-ESRGAN repos
- add a link to my repo in the footer
- could have an accordion that shows the verbose output

Feature Development
- incorporate use of Real-ESRGAN tool for frame restoration/upscaling
- for video inflation, update a total interpolated frames count based on the (estimated?) frame count of the mp4
- use simpler video-oriented terms on video inflation tab, like a selector with FPS values or multipliers
- look into running this in a Hugging Face space

Experiments
- can some lost detail, lost in deep interpolation, be recovered with multiple passes and varying the splits? 
  - Idea: use frames created adjacent to the outer frames + re-interpolation of some frames to try to bring that detail towards the center frames, where it's lost the most. Might require some kind of clever splitting and using additional adjacent real frames
- Is there a way to zero-in faster on precise frames like 1/3 and 2/3 if there's access to more video frames, via some kind of creative splitting?

Dreaming
- a tool that would take a set of raw PNG frames from a video one by one, estimate the aesthetic quality/amount of noise/visual cross-frame double-exposure compared to the equivalent frame re-synthesized using VFIformer, to automatically replace bad frames with good ones as part of an automated film restoration process
  - this is the process I used manually when creating [this video](https://youtu.be/PiLv5u1PYiE) on my [YouTube channel](https://www.youtube.com/channel/UCVuRnprazgpAgUQDTe-j0NA)

Bugs
- interpolate_series.py doesn't use the passed log function
