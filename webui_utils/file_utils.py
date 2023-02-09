import os
import glob
from zipfile import ZipFile

def create_directory(_dir):
    if not os.path.exists(_dir):
        os.makedirs(_dir)

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
    with ZipFile(filepath, "w") as zip_obj:
        for file in files:
            zip_obj.write(file, arcname=os.path.basename(file))
