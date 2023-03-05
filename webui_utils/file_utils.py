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

def _get_files(path : str):
    entries = glob.glob(path)
    files = []
    for entry in entries:
        if not os.path.isdir(entry):
            files.append(entry)
    return files

def _get_types(extension : str | list | None) -> list:
    extensions = []
    if isinstance(extension, type(None)):
        extensions.append("*")
    elif isinstance(extension, str):
        extensions += extension.split(",")
    elif isinstance(extension, list):
        extensions += extension
    result, unused = [], []
    for ext in extensions:
        if isinstance(ext, str):
            result.append(ext.strip(" ."))
        else:
            unused.append(ext)
    return list(set(result)), unused

def get_files(path : str, extension : list | str | None=None) -> list:
    """Get a list of files in the path per the extension(s)"""
    if isinstance(extension, (list, str, type(None))):
        files = []
        extensions, bad_extensions = _get_types(extension)
        if bad_extensions:
            raise ValueError("extension list items must be a strings")
        for ext in extensions:
            files += _get_files(os.path.join(path, "*." + ext))
        return files #list(set(files))
    else:
        raise ValueError("'extension' must be a string, a list of strings, or 'None'")

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
