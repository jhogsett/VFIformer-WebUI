import os
import glob
from zipfile import ZipFile

def create_directory(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def create_directories(dirs : dict):
    for key in dirs.keys():
        create_directory(dirs[key])

def get_files(path : str, extension : str = "*") -> list:
    path = os.path.join(path, "*." + extension)
    entries = glob.glob(path)
    files = []
    for entry in entries:
        if not os.path.isdir(entry):
            files.append(entry)
    return files

def get_directories(path : str) -> list:
    entries = os.listdir(path)
    directories = []
    for entry in entries:
        fullpath = os.path.join(path, entry)
        if os.path.isdir(fullpath):
            directories.append(entry)
    return directories

def create_zip(files : list, filepath : str):
    with ZipFile(filepath, "w") as zipObj:
        for file in files:
            zipObj.write(file, arcname=os.path.basename(file))

def locate_frame_file(png_files_path : str, frame_number : int):
    files = sorted(get_files(png_files_path, "png"))
    return files[frame_number]

# def split_indexed_frame_path(frame_path : str):
#     """Split a file path like path/image0123.png into path, base filename,
#        frame index and file extenstion"""
    # def split_indexed_filepath(self, filepath : str):
    #     regex = r"(.+)([1|0]\..+)(\..+$)"
    #     result = re.search(regex, filepath)
    #     if result:
    #         file_part = result.group(1)
    #         float_part = result.group(2)
    #         ext_part = result.group(3)
    #         return file_part, float(float_part), ext_part
    #     else:
    #         self.log("unable to split indexed filepath {filepath}")
    #         return None, 0.0, None
