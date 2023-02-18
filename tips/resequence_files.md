_Resequence Files_ can be used to make a set of PNG files ready for important into video editing software

# Important
The only PNG files present in the _Input Path_ should be the video frame files

- _File Type_ is used for a wildcard search of files
- _Base Filename_ is used to name the resequenced files with an added frame number
- _Starting Sequence Number_ should usually be _0_
    - A different value might be useful if inserting a PNG sequence into another
- _Integer Step_ should usually be _1_
    - This sets the increment between the added frame numbers
- _Number Padding_ should usually be _-1_ for automatic detection
    - Set to another value if a specific width of digits is needed for frame numbers
- Leave _Rename instead of duplicate files_ unchecked if the original files may be needed
    - They be useful for tracking back to a source frame
