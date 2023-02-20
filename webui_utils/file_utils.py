"""Functions for dealing with files"""
import os
import glob
from zipfile import ZipFile

def create_directory(_dir):
    """Create a directory if it does not already exist"""
    if not os.path.exists(_dir):
        os.makedirs(_dir)

def create_directories(dirs : dict):
    """Create directories stored as dict values"""
    for key in dirs.keys():
        create_directory(dirs[key])

def get_files(path : str, extension : str = "*") -> list:
    """Get a list of files in the path per the extension"""
    path = os.path.join(path, "*." + extension)
    entries = glob.glob(path)
    files = []
    for entry in entries:
        if not os.path.isdir(entry):
            files.append(entry)
    return files

def get_directories(path : str) -> list:
    """Get a list of directories in the path"""
    entries = os.listdir(path)
    directories = []
    for entry in entries:
        fullpath = os.path.join(path, entry)
        if os.path.isdir(fullpath):
            directories.append(entry)
    return directories

def create_zip(files : list, filepath : str):
    """Create a zip file from a list of files"""
    with ZipFile(filepath, "w") as zip_obj:
        for file in files:
            zip_obj.write(file, arcname=os.path.basename(file))

def locate_frame_file(png_files_path : str, frame_number : int):
    """Given a path return the file found at that sorted position"""
    files = sorted(get_files(png_files_path, "png"))
    return files[frame_number]

def split_filepath(filepath : str):
    """Split a filepath into path, filename, extension"""
    path, filename = os.path.split(filepath)
    filename, ext = os.path.splitext(filename)
    return path, filename, ext
