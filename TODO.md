## TO DO

Feature Development
- Adjacent Frame Restoration:
  - Fix two or more bad frames in a row using *targetted interpolation*
    - Example: in a set of four frames, if the middle two are bad, you wouldn't get clean interpolated replacements using their adjacent frames. 
    - Targetted interpolation could be used to recreate the bad frames at the 1/3 and 2/3 points between the two outer frames.
    - This could be extended to more frames at the cost of some loss of detail and possible inability for VFIformer to track motion
    - Note that for odd numbers of missing frames, the existing frame interpolation can be used
- Video Resynthesis:
  - Create a complete set of replacement frames for a video for use in film restoration
    - a set of replacement "even" frames is made from all the odd ones, and the same is done for new "odd" ones
    - they can be used manually to repair bad frames to restore a film
    - later, a tool could added to step through and replace bad frames

Needed
- some kind of in-progress indication on video inflation and prevention of clicking submit again
- need to be able to halt a video inflation, then resume it, picking it where it left off, either automatically, or via settings
  - could have a control to specify the number of frames to "skip" in order to resume a process
- do I need the "fix gradio phoning home" fix like in stable-diffusion-webui?
- unclutter the readme file

Nice to have
- can the core code provide a way to allow the Gradio UI to update while in progress? 
- add an about tab or page, links to VFIformer, Real-ESRGAN, Gradio and my repo
- better restart that actually reloads the model and recreates the UI (current restart is just a proof of concept)
- full auto-installation including VFIformer and Real-ESRGAN repos
- add a link to my repo in the footer
- could have an accordion that shows the verbose output
- links to useful external tools like Adobe Podcast Speed Enhancement https://podcast.adobe.com/enhance
- incorporate use of Real-ESRGAN tool for frame restoration/upscaling
- for video inflation, update a total interpolated frames count based on the (estimated?) frame count of the mp4
- use simpler video-oriented terms on video inflation tab, like a selector with FPS values or multipliers
- look into running this in a Hugging Face space

Cleanup
- PyLint
- look into referencing VFIformer inside an intact subdirectory

Experiments
- can some lost detail, lost in deep interpolation, be recovered with multiple passes and varying the splits? 
  - Idea: use frames created adjacent to the outer frames + re-interpolation of some frames to try to bring that detail towards the center frames, where it's lost the most. Might require some kind of clever splitting and using additional adjacent real frames
- Is there a way to zero-in faster on precise frames like 1/3 and 2/3 if there's access to more video frames, via some kind of creative splitting?
- something like the above could be useful if restoring a film if there are two bad frames in a row, so two of the synthesized reeplacements are unusable
  - good--bad--bad--good, four frames, but three time periods, this could be a practical use for interpolation targeting
   - it ought to be able to create two replacement frames at 1/3 and 2/3 of the distance between the outer ones!
   - call it something like double frame interpolation or Frame Restoration
     - provide frames 0 and 3, it interpolates frames 1 and 2 using interp0lation targeting, allow setting precision
- can a control be updated outside of the Gradio event loop? (might work to tap into event loop)

Dreaming
- a tool that would take a set of raw PNG frames from a video one by one, estimate the aesthetic quality/amount of noise/visual cross-frame double-exposure compared to the equivalent frame re-synthesized using VFIformer, to automatically replace bad frames with good ones as part of an automated film restoration process
  - this is the process I used manually when creating [this video](https://youtu.be/PiLv5u1PYiE) on my [YouTube channel](https://www.youtube.com/channel/UCVuRnprazgpAgUQDTe-j0NA)
- Built-in audio restoration like Adobe's Podcast Speech Enhancement https://podcast.adobe.com/enhance
- Audio Inflation to go along with Video Inflation
- Automated FPS conversion video+audio
- Effects like
  - recombine inflated frames, but combine/double-expose with frames with N frames back or forward
- Tool to split and recombine video frames to/from RGB and HSL frames
- Automatic FPS conversion using targetted interpolation smoothly moving the frames to new positions

Bugs
- (trivial) interpolate_series.py doesn't use the passed log function
