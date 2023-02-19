
- _Video Inflation_ uses _Frame Interpolation_ to double a video's frame count any number of times
- This has many useful purposes:
    - Create a Super-Slow-Motion video
    - Recover the original real-time video from a time lapse video or GIF
    - Turn discrete motion continuous, like a second hand of a ticking clock
    - Frame Rate conversion

# Important
- This process will be slow, perhaps many hours long!
- Progress will be shown in the console using a standard _tqdm_ progress bar
- The browser window can be safely closed without interupting the process
- Currently there isn't an automatic way to resume a stalled inflation
    - Suggestion:
        - Set aside the rendered frames from the _input path_
        - Re-run the inflation
        - Use the _Resequence Files_ tool to rename the the two sets of rendered frames so they can be recombined
